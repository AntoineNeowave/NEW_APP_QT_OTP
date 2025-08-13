# core/detection_worker.py
# Worker pour détecter les changements de statut du périphérique FIDO/OTP
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread

class DetectorWorker(QObject):
    device_status = pyqtSignal(bool)
    
    def __init__(self, backend, interval=1000):
        super().__init__()
        self.backend = backend
        self._running = True
        self.interval = interval
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll_device)
        self.last_status = None

    def start(self):
        self.timer.start(self.interval)

    def stop(self):
        self._running = False
        self.timer.stop()

    def _poll_device(self):
        connected = self.backend.ping_device()
        if connected != self.last_status:
            self.device_status.emit(connected)
            self.last_status = connected