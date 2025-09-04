# core/otp_model.py
# Transforme la map CBOR recue d'OTP_ENUMERATE en un objet Python
# et une méthode pour afficher les paramètres

ALG_CODE_TO_NAME = {
    4: "SHA1",
    5: "SHA256",
    7: "SHA512"
}

TYPE_NAME = {1: "HOTP", 2: "TOTP"}

class OTPGenerator:
    def __init__(self, data: dict):
        self.label = data.get(1)
        self.otp_type = data.get(2)  # 1 = HOTP, 2 = TOTP
        self.alg = data.get(3)
        self.digits = data.get(4)
        self.counter = data.get(5)
        self.period = data.get(6, 30 if self.otp_type == 2 else None)

    def display_parameters(self) -> str:
        if ":" in self.label:
            self.account, self.issuer = self.label.split(":", 1)
        else:
            self.account = self.label
            self.issuer = ""
        parts = [
            _("Type: {type_name}").format(type_name=TYPE_NAME.get(self.otp_type, '?')),
            _("Account : {account}").format(account=self.account),
            ]
        if self.issuer:
            parts.append(_("Issuer: {issuer}").format(issuer=self.issuer))
        parts.append(_("Code length: {digits}").format(digits=self.digits))
        if self.otp_type == 1:
            counter_value = int.from_bytes(self.counter, 'big') if self.counter else '?'
            parts.append(_("Counter: {counter}").format(counter=counter_value))
        elif self.otp_type == 2:
            parts.append(_("Timestep: {period} seconds").format(period=self.period))
        algo_name = ALG_CODE_TO_NAME.get(self.alg, _("Unknown ({alg})").format(alg=self.alg))
        parts.append(_("Algorithm: {algo}").format(algo=algo_name))
        return "\n".join(parts)
