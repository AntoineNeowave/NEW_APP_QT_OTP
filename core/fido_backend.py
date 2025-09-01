# core/fido_backend.py

import threading
from fido2.ctap2 import Ctap2
from fido2.hid import CtapHidDevice, CAPABILITY
from fido2.ctap import CtapError
import time
from base64 import b32decode
from fido2.pcsc import CtapPcscDevice
from core.logger import app_logger

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

class FidoOTPBackend:
    def __init__(self):
        self.lock = threading.RLock()  # RLock pour éviter les deadlocks
        self.ctap = None
        self.device = None
        self.last_error = None
        self.connection_valid = False
        self.logger = app_logger.getChild('Backend')
        self.logger.info("FidoOTPBackend initialized")
    @staticmethod
    def get_error_message(code: int) -> str:
        return OTP_ERROR_CODES.get(code, (f"Unknown error 0x{code:02X}", "Undocumented error"))[1]

    def _test_otp_support(self, ctap):
        """Teste si le device supporte les commandes OTP"""
        try:
            ctap.send_cbor(OTP_ENUMERATE, {1: 0})
            return True
        except CtapError:
            self.logger.debug(f"[DEBUG] CTAP Error during test_otp_support")
            return False
        except Exception:
            self.logger.debug(f"[DEBUG] CTAP Error during test_otp_support")
            return False

    def _connect(self):
        """Connexion thread-safe avec validation OTP"""
        # Si on a déjà une connexion valide, la tester rapidement
        if self.connection_valid and self.ctap and self.device:
            try:
                return self.ctap
            except Exception as e:
                self.logger.debug("Existing connection invalid")
                self._cleanup_connection()

        self.logger.info("Searching for FIDO2 device with OTP support...")
        self._cleanup_connection()

        # 1) Test des devices HID
        try:
            hid_devs = list(CtapHidDevice.list_devices())
            self.logger.debug(f"{len(hid_devs)} HID devices found")
        except Exception as e:
            self.logger.debug(f"[DEBUG] Erreur énumération HID: {e}")
            hid_devs = []

        for i, dev in enumerate(hid_devs):
            try:
                self.logger.debug(f"[DEBUG] Test device HID {i}: {dev}")
                ctap = Ctap2(dev)
                self.logger.debug(f"[DEBUG] CTAP2 créé pour device HID {i}")
                if self._test_otp_support(ctap):
                    self.ctap = ctap
                    self.device = dev
                    self.connection_valid = True
                    self.last_error = None
                    self.logger.debug(f"Device OTP trouvé : {dev}")
                    return self.ctap
                else:
                    self.logger.debug(f"[DEBUG] Device HID {i} ne supporte pas OTP")
                    self._cleanup_connection()
            except Exception as e:
                self.logger.debug(f"[DEBUG] Erreur avec device HID {i}: {e}")
                try: 
                    self._cleanup_connection()
                except Exception as close_e: 
                    self.logger.debug(f"[DEBUG] Erreur fermeture device HID {i}: {close_e}")

        # 2) Test des devices PC/SC
        try:
            pcsc_devs = list(CtapPcscDevice.list_devices())
            self.logger.debug(f"[DEBUG] {len(pcsc_devs)} devices PCSC trouvés")
        except Exception as e:
            self.logger.debug(f"[DEBUG] Erreur énumération PCSC: {e}")
            pcsc_devs = []

        for i, dev in enumerate(pcsc_devs):
            try:
                self.logger.debug(f"[DEBUG] Test device PCSC {i}: {dev}")
                ctap = Ctap2(dev)
                self.logger.debug(f"[DEBUG] CTAP2 créé pour device PCSC {i}")
                if self._test_otp_support(ctap):
                    self.ctap = ctap
                    self.device = dev
                    self.connection_valid = True
                    self.last_error = None
                    self.logger.debug(f"Device OTP trouvé : {dev}")
                    return self.ctap
                else:
                    self.logger.debug(f"[DEBUG] Device PCSC {i} ne supporte pas OTP")
                    self._cleanup_connection()
            except Exception as e:
                self.logger.debug(f"[DEBUG] Erreur avec device PCSC {i}: {e}")
                try: 
                    self._cleanup_connection()
                except Exception as close_e: 
                    self.logger.debug(f"[DEBUG] Erreur fermeture device PCSC {i}: {close_e}")

        # Aucun device compatible trouvé
        self.logger.debug("[DEBUG] Aucun device OTP trouvé")
        self._cleanup_connection()
        raise RuntimeError("⚠️ No OTP Device detected.")

    def _cleanup_connection(self):
        """Nettoie la connexion actuelle"""
        self.logger.debug("[DEBUG] _cleanup_connection appelé")
        self.connection_valid = False
        if self.device:
            try:
                self.logger.debug(f"[DEBUG] Fermeture device: {self.device}")
                self.device.close()
                self.logger.debug("[DEBUG] Device fermé avec succès")
            except Exception as e:
                self.logger.debug(f"[DEBUG] Erreur fermeture device: {e}")
        self.ctap = None
        self.device = None

    def _execute_command(self, command, payload, operation_name="operation"):
        """Exécute une commande CTAP avec gestion d'erreur uniforme"""
        with self.lock:
            self.logger.debug(f"Executing command: {operation_name}")
            try:
                self.logger.debug("Calling _connect()")
                ctap = self._connect()
                self.logger.debug(f"Connect OK, ctap={type(ctap).__name__}")
                self.logger.debug(f"Sending CBOR command: 0x{command:02X}")
                result = ctap.send_cbor(command, payload)
                self.logger.debug(f"CBOR command OK, result keys: {list(result.keys()) if result else 'None'}")
                return True, result
            except CtapError as e:
                error_msg = self.get_error_message(e.code)
                self.logger.warning(f"CTAP Error in {operation_name}: 0x{e.code:02X} -> {error_msg}")
                self.last_error = error_msg
                # Ne pas invalider la connexion pour les erreurs CTAP logiques
                return False, None
            except (OSError, IOError, ConnectionError) as e:
                # Erreur de communication/USB
                self.logger.error(f"Communication error in {operation_name}: {e}")
                self._cleanup_connection()
                self.last_error = "Device communication error"
                return False, None
            except (Exception, RuntimeError) as e:
                # Erreur de connexion/communication → invalider la connexion
                self.logger.warning(f"Command {operation_name} Exception / RuntimeError")
                self._cleanup_connection()
                self.last_error = str(e)
                return False, None

    def ping_device(self) -> bool:
        """Test de présence du device"""
        success, _ = self._execute_command(OTP_ENUMERATE, {1: 0}, "ping")
        return success

    def list_generators(self, index=0, count=None):
        """Liste les générateurs OTP (23 max)"""
        params = {1: index}
        if count is not None:
            params[2] = count

        success, result = self._execute_command(OTP_ENUMERATE, params, operation_name="list_generators")

        if success:
            # Si count=0, renvoyer juste le nombre total
            if params.get(2, None) == 0:
                return result.get(1, 0)
            return result.get(2, [])  # otpGenerators
        elif success is False:  # Erreur CTAP
            return False
        else:  # Erreur de connexion
            return None
        
    def get_all_generators(self):
        """Récupère tous les générateurs OTP"""
        try:
            all_generators = []

            # 1. Récupérer le nombre total (exactement comme dans votre worker)
            total = self.list_generators(index=0, count=0)
            if total is None or total is False or not isinstance(total, int):
                return None

            batch_size = 23
            index = 0

            # 2. Lire par batchs (exactement comme dans votre worker)
            while index < total:
                count = min(batch_size, total - index)
                batch = self.list_generators(index=index, count=count)
                if batch is None:
                    return None
                elif batch is False:
                    # Erreur CTAP sur ce batch, continuer avec le batch suivant
                    index += count
                    continue

                all_generators.extend(batch)
                index += len(batch)

            return all_generators
            
        except Exception as e:
            self.logger.debug(f"Error in get_all_generators: {e}")
            self.last_error = str(e)
            return None

    def generate_code(self, label: str, otp_type: int, period: int = None):
        """Génère un code OTP"""
        payload = {1: label}
        if otp_type == 2:  # TOTP
            T = int(time.time()) // (period or 30)
            payload[2] = T.to_bytes(8, 'big')
        
        success, result = self._execute_command(OTP_GENERATE, payload, f"generate_code({label})")
        if success:
            return result.get(1, "?")
        elif success is False:  # Erreur CTAP
            return False
        else:  # Erreur de connexion
            return None

    def delete_generator(self, label: str) -> bool:
        """Supprime un générateur"""
        payload = {1: label}
        success, _ = self._execute_command(OTP_DELETE, payload, f"delete_generator({label})")
        return success

    def create_generator(self, label: str, otp_type: str, secret_b32: str, algo: str,
                        digits: int = 6, counter: int = None, period: int = None) -> bool:
        """Crée un nouveau générateur"""
        try:
            secret = b32decode(secret_b32, casefold=True)
        except Exception as e:
            self.logger.debug(f"Base32 decoding error : {e}")
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

        success, _ = self._execute_command(OTP_CREATE, payload, f"create_generator({label})")
        return success