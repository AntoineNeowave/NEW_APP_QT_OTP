# core/otp_refresh_worker.py
# thread de rafraîchissement qui protège l’UI des I/O lents.

from PyQt6.QtCore import QObject, pyqtSignal
from core.otp_model import OTPGenerator

class OTPRefreshWorker(QObject):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    device_status_changed = pyqtSignal(bool)  # Nouveau signal pour l'état de connexion

    def __init__(self, backend):
        super().__init__()
        self.backend = backend

    def run(self):
        """Execute le refresh avec gestion de la connexion/déconnexion"""
        try:
            all_generators = self.backend.get_all_generators()
            
            if all_generators is None:
                # Erreur de connexion
                self.device_status_changed.emit(False)
                error_message = getattr(self.backend, "last_error", "Device not detected")
                self.error.emit(error_message)
                return
            elif all_generators is False:
                # Erreur CTAP
                self.device_status_changed.emit(False)
                error_message = getattr(self.backend, "last_error", "CTAP error")
                self.error.emit(error_message)
                return

            # Traiter chaque générateur
            result = []
            for g in all_generators:
                try:
                    generator = OTPGenerator(g)
                    
                    # Générer le code seulement pour les TOTP
                    if generator.otp_type == 2:  # TOTP
                        code = self.backend.generate_code(generator.label, generator.otp_type, generator.period)
                        generator.code = code if code else "Error"
                    elif generator.otp_type == 1:  # HOTP
                        generator.code = "●●●●●●"  # Code par défaut pour HOTP
                        
                    result.append(generator)
                except Exception as e:
                    # Si erreur sur un générateur spécifique, continuer avec les autres
                    print(f"Error for generator {g.get(1, 'unknown')}: {e}")
                    continue

            self.finished.emit(result)
            
        except Exception as e:
            self.device_status_changed.emit(False)
            error_message = getattr(self.backend, "last_error", "Device not detected")
            self.error.emit(error_message)