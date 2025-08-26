# core/fido_backend.py - Version corrigée simple

import threading
from fido2.ctap2 import Ctap2
from fido2.hid import CtapHidDevice, CAPABILITY
from fido2.ctap import CtapError
import time
from base64 import b32decode
from fido2.pcsc import CtapPcscDevice
import signal

OTP_CREATE = 0xB1
OTP_GENERATE = 0xB2
OTP_DELETE = 0xB3
OTP_ENUMERATE = 0xB4

ALG_NAME_TO_CODE = {"SHA1": 4, "SHA256": 5, "SHA512": 7}
TYPE_NAME_TO_CODE = {"HOTP": 1, "TOTP": 2}

OTP_ERROR_CODES = {
    0x00: ("OTP_OK", "Command executed successfully"),
    0x01: ("ERR_INVALID_CMD", "Command not recognized"),
    0xF1: ("OTP_ERR_INVALID_CBOR", "The command contains invalid CBOR encoding"),
    0xF2: ("OTP_ERR_INVALID_COMMAND", "Unrecognized OTP command"),
    0xF3: ("OTP_ERR_INVALID_PARAMETER", "Invalid parameter in command"),
    0xF4: ("OTP_ERR_GENERATOR_EXISTS", "A generator with this name already exists"),
    0xF5: ("OTP_ERR_GENERATOR_NOT_FOUND", "Generator not found"),
    0xF6: ("OTP_ERR_MEMORY_FULL", "Memory full, unable to create another generator"),
}

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timeout")

class FidoOTPBackend:
    def __init__(self):
        self.lock = threading.RLock()
        self.ctap = None
        self.device = None
        self.last_error = None
        self.connection_valid = False

    @staticmethod
    def get_error_message(code: int) -> str:
        return OTP_ERROR_CODES.get(code, (f"Unknown error 0x{code:02X}", "Undocumented error"))[1]

    def _test_otp_support(self, ctap):
        """Teste si le device supporte les commandes OTP avec timeout court"""
        try:
            # Test très rapide pour le support OTP
            ctap.send_cbor(OTP_ENUMERATE, {1: 0})
            return True
        except CtapError:
            return False
        except Exception:
            return False

    def _connect(self):
        """Connexion thread-safe avec validation OTP"""
        # Si on a déjà une connexion valide, la tester rapidement
        if self.connection_valid and self.ctap and self.device:
            try:
                # Test rapide de la connexion sans timeout pour éviter les blocages
                self.ctap.send_cbor(OTP_ENUMERATE, {1: 0})
                return self.ctap
            except:
                # Connexion invalide, on va reconnecter
                self._cleanup_connection()

        print("Recherche d'un device FIDO2 avec support OTP...")
        self._cleanup_connection()

        # HID d'abord
        hid_devs = list(CtapHidDevice.list_devices() or [])
        if hid_devs:
            for dev in hid_devs:
                try:
                    ctap = Ctap2(dev)
                    if self._test_otp_support(ctap):
                        self.ctap, self.device = ctap, dev
                        self.connection_valid = True
                        print("✅ Device HID OTP connecté")
                        return self.ctap
                except Exception as e:
                    print(f"Erreur test HID device: {e}")
                    try:
                        dev.close()
                    except:
                        pass

        # Si aucun HID valide → PCSC
        pcsc_devs = list(CtapPcscDevice.list_devices() or [])
        if pcsc_devs:
            for dev in pcsc_devs:
                try:
                    ctap = Ctap2(dev)
                    if self._test_otp_support(ctap):
                        self.ctap, self.device = ctap, dev
                        self.connection_valid = True
                        print("✅ Device PCSC OTP connecté")
                        return self.ctap
                except Exception as e:
                    print(f"Erreur test PCSC device: {e}")
                    try:
                        dev.close()
                    except:
                        pass

        raise RuntimeError("⚠️ No OTP Device detected.")
    
    def _cleanup_connection(self):
        """Nettoie la connexion actuelle"""
        self.connection_valid = False
        if self.device:
            try:
                self.device.close()
            except:
                pass
        self.ctap = None
        self.device = None
        time.sleep(0.1)  # Petite pause

    def _execute_command(self, command, payload, operation_name="operation"):
        """Exécute une commande CTAP avec timeout"""
        with self.lock:
            try:
                ctap = self._connect()
                
                # Timeout avec threading
                result = [None]
                exception = [None]
                
                def run_command():
                    try:
                        result[0] = ctap.send_cbor(command, payload)
                    except Exception as e:
                        exception[0] = e
                
                thread = threading.Thread(target=run_command, daemon=True)
                thread.start()
                thread.join(timeout=4.0)
                
                if thread.is_alive():
                    # Timeout atteint
                    print(f"⏰ Timeout sur {operation_name}")
                    self.last_error = f"Timeout during {operation_name}"
                    self._cleanup_connection()
                    return False, None
                
                if exception[0]:
                    raise exception[0]
                    
                return True, result[0]
                
            except CtapError as e:
                error_msg = self.get_error_message(e.code)
                print(f"CTAP Error during {operation_name}: {e.code:02X} → {error_msg}")
                self.last_error = error_msg
                return False, None
            except (Exception, RuntimeError) as e:
                print(f"Connection error during {operation_name}: {e}")
                self._cleanup_connection()
                self.last_error = str(e)
                return False, None

    def ping_device(self) -> bool:
        """Test de présence du device"""
        with self.lock:                
            # Test rapide sans timeout lourd
            if self.connection_valid and self.ctap:
                try:
                    # Test minimal sans attendre
                    self.ctap.send_cbor(OTP_ENUMERATE, {1: 0})
                    return True
                except:
                    self.connection_valid = False
                    return False
            else:
                # Pas de connexion établie
                return False

    def list_generators(self):
        """Liste les générateurs OTP"""
        success, result = self._execute_command(OTP_ENUMERATE, {}, "list_generators")
        if success:
            return result.get(2, [])
        elif success is False:  # Erreur CTAP
            return False
        else:  # Erreur de connexion
            return None

    def generate_code(self, label: str, otp_type: int, period: int = None):
        """Génère un code OTP"""
        payload = {1: label}
        if otp_type == 2:  # TOTP
            T = int(time.time()) // (period or 30)
            payload[2] = T.to_bytes(8, 'big')
        
        success, result = self._execute_command(
            OTP_GENERATE, payload, f"generate_code({label})"
        )
        if success:
            return result.get(1, "?")
        elif success is False:  # Erreur CTAP
            return False
        else:  # Erreur de connexion
            return None

    def delete_generator(self, label: str) -> bool:
        """Supprime un générateur"""
        payload = {1: label}
        success, _ = self._execute_command(
            OTP_DELETE, payload, f"delete_generator({label})"
        )
        return success

    def create_generator(self, label: str, otp_type: str, secret_b32: str, algo: str,
                        digits: int = 6, counter: int = None, period: int = None) -> bool:
        """Crée un nouveau générateur"""
        try:
            secret = b32decode(secret_b32, casefold=True)
        except Exception as e:
            print(f"Base32 decoding error : {e}")
            self.last_error = str(e)
            return False

        payload = {
            1: label,
            2: TYPE_NAME_TO_CODE[otp_type],
            3: {
                1: 4,  # kty = Symmetric
                3: ALG_NAME_TO_CODE[algo],
                -1: secret,
            },
            4: digits,
        }

        if otp_type == "HOTP" and counter is not None:
            payload[5] = int(counter).to_bytes(8, "big")
        if otp_type == "TOTP" and period is not None:
            payload[6] = period

        success, _ = self._execute_command(
            OTP_CREATE, payload, f"create_generator({label})"
        )
        return success