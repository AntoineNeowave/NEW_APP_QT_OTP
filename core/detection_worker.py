# core/detection_worker.py
# thread de rafraîchissement qui protège l’UI des I/O lents.
# Fait un ping sur le device FIDO toutes les 5 secondes pour vérifier sa présence.

from PyQt6.QtCore import QObject, pyqtSignal
from core.otp_model import OTPGenerator

class OTPDetectionWorker(QObject):
    error = pyqtSignal(str)
    device_status_changed = pyqtSignal(bool)  # Nouveau signal pour l'état de connexion

    def __init__(self, backend):
        super().__init__()
        self.backend = backend

    def run(self):
        """Execute le refresh avec gestion de la connexion/déconnexion"""
        try:
            # Tenter de lister les générateurs
            raw = self.backend.list_generators()
            
            if raw is None:
                # Erreur de connexion - device probablement déconnecté
                error_message = getattr(self.backend, "last_error", "Device non détecté")
                self.device_status_changed.emit(False)
                self.error.emit(error_message)
                return
            
            if raw is False:
                # Erreur CTAP mais device connecté
                error_message = getattr(self.backend, "last_error", "Erreur CTAP")
                self.device_status_changed.emit(True)  # Device présent mais erreur
                self.error.emit(error_message)
                return
            
            # Device connecté et fonctionnel
            self.device_status_changed.emit(True)
            
            if not raw:  # Liste vide
                self.finished.emit([])
                return
            
        except Exception as e:
            # Erreur générale - probablement device déconnecté
            self.device_status_changed.emit(False)
            self.error.emit(f"Erreur générale: {str(e)}")