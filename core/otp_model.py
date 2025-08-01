# core/otp_model.py
class OTPGenerator:
    def __init__(self, data: dict):
        self.label = data.get(1)
        self.otp_type = data.get(2)  # 1 = HOTP, 2 = TOTP
        self.alg = data.get(3)
        self.digits = data.get(4)
        self.counter = data.get(5)
        self.period = data.get(6, 30 if self.otp_type == 2 else None)

    def display_subtitle(self) -> str:
        parts = [f"{self.digits} digits"]
        if self.otp_type == 1:
            parts.append(f"Counter: {int.from_bytes(self.counter, 'big') if self.counter else '?'}")
        elif self.otp_type == 2:
            parts.append(f"Period: {self.period}s")
        return " | ".join(parts)
