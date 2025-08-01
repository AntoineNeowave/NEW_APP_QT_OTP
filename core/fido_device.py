# core/fido_device.py
import threading
from fido2.ctap2 import Ctap2
from fido2.hid import CtapHidDevice, CAPABILITY
from fido2.ctap import CtapError
import time

OTP_CREATE = 0xB1
OTP_GENERATE = 0xB2
OTP_DELETE = 0xB3
OTP_ENUMERATE = 0xB4

class FidoOTPBackend:
    def __init__(self):
        self.lock = threading.Lock()
        self.ctap = self._connect()

    def _connect(self):
        dev = next(CtapHidDevice.list_devices(), None)
        if not dev or not (dev.capabilities & CAPABILITY.CBOR):
            raise RuntimeError("Token FIDO2 non détecté ou incompatible.")
        return Ctap2(dev)

    def list_generators(self):
        with self.lock:
            try:
                resp = self.ctap.send_cbor(OTP_ENUMERATE, {})
                return resp.get(2, [])
            except CtapError as e:
                print(f"Erreur CTAP ENUMERATE: 0x{e.code:02X}")
                return []
            except Exception as e:
                print(f"Erreur générale: {e}")
                return []

    def generate_code(self, label: str, otp_type: int, period: int = None):
        with self.lock:
            try:
                payload = {1: label}
                if otp_type == 2:  # TOTP
                    T = int(time.time()) // (period or 30)
                    payload[2] = T.to_bytes(8, 'big')
                resp = self.ctap.send_cbor(OTP_GENERATE, payload)
                return resp.get(1, "?")
            except CtapError as e:
                return f"Err:0x{e.code:02X}"
            except Exception as e:
                return f"Err:{str(e)}"
