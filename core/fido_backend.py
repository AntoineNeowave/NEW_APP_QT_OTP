# core/fido_device.py

# Opérations FIDO/OTP,  passerelle thread sécurisée pour les opérations I/O lentes. 
import threading
from fido2.ctap2 import Ctap2
from fido2.hid import CtapHidDevice, CAPABILITY
from fido2.ctap import CtapError
import time
from base64 import b32decode
from fido2.pcsc import CtapPcscDevice

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
        self.lock = threading.Lock()  # Une commande CTAP à la fois, sinon, crash

    @staticmethod
    def get_error_message(code: int) -> str:
        return OTP_ERROR_CODES.get(code, (f"Unknown error 0x{code:02X}", "Undocumented error"))[1]

    def _connect(self):
        # si self.ctap existe déjà, on la réutilise
        if hasattr(self, "ctap") and self.ctap:
            return self.ctap

        dev = next(CtapHidDevice.list_devices(), None)
        if not dev:
            dev = next(CtapPcscDevice.list_devices(), None)
        if not dev or not (dev.capabilities & CAPABILITY.CBOR):
            raise RuntimeError("🔌 No OTP Device detected.")
        self.ctap = Ctap2(dev)
        return self.ctap

    def ping_device(self) -> bool:
        with self.lock:
            try:
                ctap = self._connect()
                ctap.send_cbor(OTP_ENUMERATE, {1: 0})
                return True
            except CtapError as e:
                self.last_error = self.get_error_message(e.code)
                return False
            except Exception as e:
                self.ctap = None
                self.last_error = str(e)
                return False

    def list_generators(self):
        with self.lock:
            try:
                ctap = self._connect()
                resp = ctap.send_cbor(OTP_ENUMERATE, {})
                return resp.get(2, [])
            except CtapError as e:
                print(f"CTAP Error : {e.code:02X} → {self.get_error_message(e.code)}")
                self.last_error = self.get_error_message(e.code)
                return False

            except Exception as e:
                self.ctap = None
                self.last_error = str(e)
                return None

    def generate_code(self, label: str, otp_type: int, period: int = None):
        with self.lock:
            try:
                ctap = self._connect()
                payload = {1: label}
                if otp_type == 2:  # TOTP
                    T = int(time.time()) // (period or 30)
                    payload[2] = T.to_bytes(8, 'big')
                resp = ctap.send_cbor(OTP_GENERATE, payload)
                return resp.get(1, "?")
            except CtapError as e:
                print(f"CTAP Error : {e.code:02X} → {self.get_error_message(e.code)}")
                self.last_error = self.get_error_message(e.code)
                return False
            except Exception as e:
                self.ctap = None
                self.last_error = str(e)
                return None

    def delete_generator(self, label: str) -> bool:
        with self.lock:
            try:
                ctap = self._connect()
                payload = {1: label}
                ctap.send_cbor(OTP_DELETE, payload)
                return True
            except CtapError as e:
                print(f"CTAP Error : {e.code:02X} → {self.get_error_message(e.code)}")
                self.last_error = self.get_error_message(e.code)
                return False
            except Exception as e:
                self.ctap = None
                self.last_error = str(e)
                return False

    def create_generator(self, label: str, otp_type: str, secret_b32: str, algo: str,
                        digits: int = 6, counter: int = None, period: int = None) -> bool:

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

        with self.lock:
            try:
                ctap = self._connect()
                ctap.send_cbor(OTP_CREATE, payload)
                return True
            except CtapError as e:
                print(f"CTAP Error : {e.code:02X} → {self.get_error_message(e.code)}")
                self.last_error = self.get_error_message(e.code)
                return False
            except Exception as e:
                self.ctap = None
                self.last_error = str(e)
                return False
