# core/otp_model.py
ALG_CODE_TO_NAME = {
    4: "SHA1",
    5: "SHA256",
    7: "SHA512"
}

class OTPGenerator:
    def __init__(self, data: dict):
        self.label = data.get(1)
        self.otp_type = data.get(2)  # 1 = HOTP, 2 = TOTP
        self.alg = data.get(3)
        self.digits = data.get(4)
        self.counter = data.get(5)
        self.period = data.get(6, 30 if self.otp_type == 2 else None)

    def display_parameters(self) -> str:
        parts = [f"User : {self.label}", f"Code length : {self.digits}"]
        if self.otp_type == 1:
            counter_value = int.from_bytes(self.counter, 'big') if self.counter else '?'
            parts.append(f"Counter : {counter_value}")
        elif self.otp_type == 2:
            parts.append(f"Timestep : {self.period} seconds")
        algo_name = ALG_CODE_TO_NAME.get(self.alg, f"Unknown({self.alg})")
        parts.append(f"Algorithm: {algo_name}")
        return "\n".join(parts)
