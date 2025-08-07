# core/otp_refresh_worker.py
from PyQt6.QtCore import QObject, pyqtSignal
from core.otp_model import OTPGenerator

class OTPRefreshWorker(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, backend):
        super().__init__()
        self.backend = backend

    def run(self):
        raw = self.backend.list_generators()

        if raw is None or raw is False:
            self.error.emit(getattr(self.backend, "last_error", "Erreur inconnue"))
            return

        result = []
        for g in raw:
            generator = OTPGenerator(g)
            code = self.backend.generate_code(generator.label, generator.otp_type, generator.period)
            generator.code = code if code else "Erreur"
            result.append(generator)

        self.finished.emit(result)
