# core/detection_worker.py
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread, Qt, pyqtSlot

class DetectorWorker(QObject):
    device_status = pyqtSignal(bool)
    
    def __init__(self, backend, interval=1000):
        super().__init__()
        self.backend = backend
        self.interval = interval
        self.timer = None
        self.last_status = None

    @pyqtSlot()
    def start(self):
        # Créé le QTimer dans le thread du worker
        if self.timer is None:
            self.timer = QTimer(self)
            self.timer.setInterval(self.interval)
            self.timer.setTimerType(Qt.TimerType.CoarseTimer)
            self.timer.timeout.connect(self._poll_device)
        if not self.timer.isActive():
            self.timer.start()

    @pyqtSlot()
    def stop(self):
        # Appelé depuis le GUI via Queued → s’exécute côté worker
        if self.timer and self.timer.isActive():
            self.timer.stop()

    @pyqtSlot()
    def cleanup(self):
        # Arrêt + destruction du timer dans SON propre thread
        if self.timer:
            if self.timer.isActive():
                self.timer.stop()
            self.timer.deleteLater()
            self.timer = None

    def _poll_device(self):
        connected = self.backend.ping_device()
        if connected != self.last_status:
            self.device_status.emit(connected)
            self.last_status = connected
