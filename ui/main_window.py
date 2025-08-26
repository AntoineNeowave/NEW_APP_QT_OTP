# ui/main_window.py
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QScrollArea, QPushButton, QMessageBox, QStackedLayout, QLineEdit
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QTimer, QSize, QThread, QMetaObject, QMutex
from ui.otp_card import OTPCard
from ui.enroll_widget import EnrollWidget
from core.fido_backend import FidoOTPBackend
from core.otp_refresh_worker import OTPRefreshWorker
from core.detection_worker import DetectorWorker
from ui.header import Header
from ui.ressources import resource_path

import time


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Winkeo/Badgeo OTP Manager - V0.0.5")
        logo_path = resource_path("images", "logo.png")
        self.setWindowIcon(QIcon(str(logo_path)))
        self.setFixedSize(400, 650)
        flags = self.windowFlags()
        self.setWindowFlags(flags | Qt.WindowType.MSWindowsFixedSizeDialogHint)

        self.backend = FidoOTPBackend()
        self.generator_widgets = {}

        self.refresh_mutex = QMutex()
        self.current_refresh_thread = None

        # Pour une interface à onglets
        self.stack = QStackedLayout()
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self.stack)

        self.main_view = QWidget(self)
        main_view_layout = QVBoxLayout(self.main_view)
        self.stack.addWidget(self.main_view)

        # Header
        header_widget = Header()     
        main_view_layout.addWidget(header_widget)

        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_view_layout.setContentsMargins(0, 0, 0, 0)
        main_view_layout.setSpacing(0)

        # boutton enrol et searchbar
        enrol_search_widget = QWidget()
        enrol_search_widget.setObjectName("enrolSeach")
        enrol_search_layout = QHBoxLayout(enrol_search_widget)
        add_account_path = resource_path("images", "add_account.png")
        add_account_path_clicked = resource_path("images", "add_account_clicked.png")
        enrol_button = IconButton(add_account_path, add_account_path_clicked)
        enrol_button.setObjectName("enrolPageButton")
        search_bar = QLineEdit()
        search_bar.setObjectName("searchBar")
        search_bar.setPlaceholderText("Search for a code...")
        search_bar.setClearButtonEnabled(True)
        search_bar.textChanged.connect(self.on_search_text_changed)
        search_bar.setMinimumWidth(250)
        enrol_search_layout.addWidget(enrol_button, alignment=Qt.AlignmentFlag.AlignLeft)
        enrol_search_layout.addStretch()
        enrol_search_layout.addWidget(search_bar)
        enrol_search_layout.addStretch()
        enrol_button.clicked.connect(self.switch_to_enroll_view)
        main_view_layout.addWidget(enrol_search_widget)

        # Status présence du device
        self.status_label = QLabel()
        self.status_label.setObjectName("statusKey")
        self.status_label.hide()
        main_view_layout.addWidget(self.status_label)

        # OTP list area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.otp_list_widget = QWidget()
        self.otp_list_widget.setObjectName("listArea")
        self.otp_list_layout = QVBoxLayout(self.otp_list_widget)
        self.otp_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.otp_list_layout.setSpacing(10) # espacement entre les cartes 
        scroll_area.setWidget(self.otp_list_widget)
        main_view_layout.addWidget(scroll_area, stretch=1)

        # === Vue d'enrôlement ===
        self.enroll_widget = EnrollWidget(self.backend, self)
        self.enroll_widget.seed_enrolled.connect(self.on_enroll_success)
        self.enroll_widget.cancel_requested.connect(self.switch_to_main_view)
        self.stack.addWidget(self.enroll_widget)

        self.last_totp_cycles = {}  # label -> dernier cycle vu
        self.pending_refresh = False  # Flag pour éviter les refresh multiples
        self.operation_in_progress = False  # Flag pour les opérations utilisateur
        self.operation_timer = None  # Timer pour les opérations en attente

        # Timer pour les barres de progression TOTP
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress_bars)
        self.progress_timer.start(20)

        # Timer séparé pour forcer les refresh périodiques (backup)
        self.backup_refresh_timer = QTimer(self)
        self.backup_refresh_timer.timeout.connect(self.force_totp_refresh)
        self.backup_refresh_timer.start(1000)  # Chaque seconde

        # Première tentative de connexion
        self.start_refresh_thread()

        #Detection des devices
        self.setup_detection_thread()

    def setup_detection_thread(self):
        self.detection_thread = QThread()
        self.detector = DetectorWorker(self.backend)
        self.detector.moveToThread(self.detection_thread)

        self.detection_thread.started.connect(self.detector.start)
        self.detector.device_status.connect(self._handle_detection_result)

        self.detection_thread.start()
        
    def _handle_detection_result(self, connected: bool):
        if connected:
            self.start_refresh_thread()
            self.status_label.hide()
            self.set_cards_online()
        else:
            self.status_label.setText("⚠️ No OTP Device detected.")
            self.status_label.show()
            self.set_cards_offline("Device disconnected")

    def set_cards_offline(self, reason: str):
        for card in self.generator_widgets.values():
            card.set_offline(reason)

    def set_cards_online(self):
        for card in self.generator_widgets.values():
            card.set_online()

    def update_progress_bars(self):
        """Met à jour les barres de progression et détecte les nouveaux cycles TOTP"""
        # Ne pas déclencher de refresh auto pendant une opération utilisateur
        if self.operation_in_progress:
            return
            
        now = time.time()
        needs_refresh = False
        
        for card in self.generator_widgets.values():
            if card.otp_type == 2:  # TOTP seulement
                card.update_progress_value(now)
                
                # Calculer le cycle actuel
                current_cycle = int(now // card.period)
                label = card.label_text
                
                # Vérifier si on est dans un nouveau cycle
                if label not in self.last_totp_cycles:
                    self.last_totp_cycles[label] = current_cycle
                elif self.last_totp_cycles[label] != current_cycle:
                    self.last_totp_cycles[label] = current_cycle
                    needs_refresh = True
        
        # Déclencher refresh si nouveau cycle détecté
        if needs_refresh and not self.pending_refresh:
            self.start_refresh_thread()
        
    def on_search_text_changed(self, text):
        for label, card in self.generator_widgets.items():
            card.setVisible(text.lower() in label.lower())

    def switch_to_enroll_view(self):
        self.stack.setCurrentWidget(self.enroll_widget)

    def switch_to_main_view(self):
        self.stack.setCurrentWidget(self.main_view)

    def on_enroll_success(self):
        """Appelé après un enrôlement réussi"""
        self.operation_in_progress = True
        
        # Attendre que les refresh en cours se terminent
        if self.pending_refresh:
            # Arrêter l'ancien timer s'il existe
            if self.operation_timer:
                self.operation_timer.stop()
                self.operation_timer.deleteLater()
            
            # Créer un timer pour attendre
            self.operation_timer = QTimer()
            self.operation_timer.setSingleShot(True)
            self.operation_timer.timeout.connect(self._complete_enroll_operation)
            self.operation_timer.start(100)  # Vérifier toutes les 100ms
        else:
            self._complete_enroll_operation()

    def _complete_enroll_operation(self):
        """Finalise l'opération d'enrôlement"""
        if self.pending_refresh:
            # Encore en cours, re-programmer
            if self.operation_timer:
                self.operation_timer.stop()
                self.operation_timer.deleteLater()
            
            self.operation_timer = QTimer()
            self.operation_timer.setSingleShot(True)
            self.operation_timer.timeout.connect(self._complete_enroll_operation)
            self.operation_timer.start(100)
            return
            
        self.start_refresh_thread()
        QTimer.singleShot(500, self._reset_operation_flag)  # Reset après 500ms
        self.switch_to_main_view()

    def force_totp_refresh(self):
        """Timer de backup pour forcer le refresh des TOTP toutes les secondes"""
        # Ne pas forcer pendant une opération utilisateur
        if self.operation_in_progress:
            return
            
        now = time.time()
        
        # Vérifier si on a des TOTP qui devraient être rafraîchis
        for card in self.generator_widgets.values():
            if card.otp_type == 2:  # TOTP seulement
                cycle_position = now % card.period
                
                # Si on est dans les 2 premières secondes du cycle et pas de refresh récent
                if cycle_position < 2.0 and not self.pending_refresh:
                    current_cycle = int(now // card.period)
                    label = card.label_text
                    
                    if (label not in self.last_totp_cycles or 
                        self.last_totp_cycles[label] != current_cycle):
                        self.start_refresh_thread()
                        break

    def start_refresh_thread(self):
        if self.pending_refresh:
            return
        
        if not self.refresh_mutex.tryLock():
            return  # Si un rafraîchissement est déjà en cours, on ne fait rien
        try:
            if (hasattr(self, 'current_refresh_thread') and 
                self.current_refresh_thread is not None and 
                self.current_refresh_thread.isRunning()):
                return
            self.pending_refresh = True

            """Lance le worker dans un thread séparé"""
            self.current_refresh_thread = QThread()
            self.worker = OTPRefreshWorker(self.backend)
            self.worker.moveToThread(self.current_refresh_thread)

            self.current_refresh_thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_refresh_data_ready)
            self.worker.error.connect(self.on_refresh_error)
            self.worker.device_status_changed.connect(self._handle_detection_result)
            
            # Nettoyage
            self.worker.finished.connect(self.current_refresh_thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker.finished.connect(self.reset_pending_refresh)
            self.worker.error.connect(self.current_refresh_thread.quit)
            self.worker.error.connect(self.worker.deleteLater)
            self.worker.error.connect(self.reset_pending_refresh)
            self.current_refresh_thread.finished.connect(self.current_refresh_thread.deleteLater)
            self.current_refresh_thread.finished.connect(self.on_worker_thread_finished)
            
            self.current_refresh_thread.start()
        finally:
            self.refresh_mutex.unlock()

    def on_worker_thread_finished(self):
        """Appelé quand le worker se termine"""
        self.current_refresh_thread = None

    def reset_pending_refresh(self):
        """Reset le flag de refresh en cours"""
        self.pending_refresh = False

    def on_refresh_data_ready(self, generators):
        """Met à jour l'UI avec les nouvelles données"""
        self.status_label.hide()
        
        existing = set(self.generator_widgets.keys())
        active = set()

        for g in generators:
            label = g.label
            active.add(label)

            if label not in self.generator_widgets:
                card = OTPCard(
                    label=g.label,
                    code=g.code,
                    parameters=g.display_parameters(),
                    otp_type=g.otp_type,
                    period=g.period
                )
                card.request_code.connect(lambda l=g.label, t=g.otp_type, p=g.period: self.update_hotp(l, t, p))
                card.delete_requested.connect(self.confirm_delete)
                card.parameters_requested.connect(lambda l=g.label, t=g.otp_type: self.on_parameters_requested(l, t))
                self.otp_list_layout.addWidget(card)
                self.generator_widgets[label] = card

                if g.otp_type == 2:
                    self.last_totp_cycles[label] = int(time.time() // g.period)
            else:
                # Mettre à jour le code seulement pour TOTP
                if g.otp_type == 2:  # TOTP
                    self.generator_widgets[label].set_code(g.code)
                # Pour HOTP, ne pas mettre à jour automatiquement

        # Supprimer les cartes qui n'existent plus
        for old_label in existing - active:
            card = self.generator_widgets.pop(old_label)
            if old_label in self.last_totp_cycles:
                del self.last_totp_cycles[old_label]
            card.setParent(None)
            card.deleteLater()

    def on_refresh_error(self, message):
        """Gère les erreurs de refresh"""
        self.status_label.setText(f"{message}")
        self.status_label.show()
        self.set_cards_offline("Device disconnected")

    def clear_all_cards(self):
        """Vide toutes les cartes OTP"""
        for card in self.generator_widgets.values():
            card.setParent(None)
            card.deleteLater()
        self.generator_widgets.clear()

    def update_hotp(self, label, otp_type, period):
        # Pour HOTP, on fait un appel direct et rapide
        code = self.backend.generate_code(label, otp_type, period)
        if code is None:
            code = f"{getattr(self.backend, 'last_error', 'Unknown')}"
        elif code is False:
            code = "Device unplugged"

        if label in self.generator_widgets:
            self.generator_widgets[label].set_code(code)

    def on_parameters_requested(self, label: str, otp_type: int):
        """Affiche les paramètres ; pour HOTP, on les rafraîchit à la demande."""
        card = self.generator_widgets.get(label)
        if not card:
            return

        if otp_type == 1:  # HOTP : rafraîchir les paramètres depuis le device
            gens = self.backend.list_generators()
            if gens:
                desc = next((g for g in gens if g.get(1) == label), None)
                if desc:
                    from core.otp_model import OTPGenerator
                    card.parameter_text = OTPGenerator(desc).display_parameters()
            # si gens est None/False, on garde l'ancien texte
        card.show_parameters()

    def confirm_delete(self, label):
        """Confirmation et suppression d'un générateur"""
        if ":" in label:
            account, issuer = label.split(":", 1)
        else:
            account = label
            issuer = ""
            
        reply = QMessageBox.question(
            self,
            f"Delete {account}",
            f"Are you sure you want to delete the OTP generator '{account}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.operation_in_progress = True
            self.pending_delete_label = label
            
            # Attendre que les refresh en cours se terminent
            if self.pending_refresh:
                # Arrêter l'ancien timer s'il existe
                if self.operation_timer:
                    self.operation_timer.stop()
                    self.operation_timer.deleteLater()
                
                # Créer un timer pour attendre
                self.operation_timer = QTimer()
                self.operation_timer.setSingleShot(True)
                self.operation_timer.timeout.connect(self._complete_delete_operation)
                self.operation_timer.start(100)
            else:
                self._complete_delete_operation()

    def _complete_delete_operation(self):
        """Finalise l'opération de suppression"""
        if self.pending_refresh:
            # Encore en cours, re-programmer
            if self.operation_timer:
                self.operation_timer.stop()
                self.operation_timer.deleteLater()
            
            self.operation_timer = QTimer()
            self.operation_timer.setSingleShot(True)
            self.operation_timer.timeout.connect(self._complete_delete_operation)
            self.operation_timer.start(100)
            return
            
        label = self.pending_delete_label
        
        success = self.backend.delete_generator(label)
        if success:
            # Nettoyer le tracking du cycle supprimé
            if label in self.last_totp_cycles:
                del self.last_totp_cycles[label]
            
            self.start_refresh_thread()
            QTimer.singleShot(500, self._reset_operation_flag)  # Reset après 500ms
        else:
            error_msg = getattr(self.backend, "last_error", f"Deletion of '{label}' failed")
            QMessageBox.warning(self, "Error", error_msg)
            self._reset_operation_flag()

    def _reset_operation_flag(self):
        """Reset le flag d'opération en cours"""
        self.operation_in_progress = False
        
        # Nettoyer le timer d'opération s'il existe
        if self.operation_timer:
            self.operation_timer.stop()
            self.operation_timer.deleteLater()
            self.operation_timer = None
        
    def closeEvent(self, event):
        """Nettoyage à la fermeture"""
        # Arrêter les timers
        if self.operation_timer:
            self.operation_timer.stop()
            self.operation_timer.deleteLater()
            
        # Arrêt du thread de détection
        try:
            if getattr(self, "detector", None):
                # stop + cleanup exécutés DANS le thread du worker
                QMetaObject.invokeMethod(self.detector, "stop", Qt.ConnectionType.QueuedConnection)
                QMetaObject.invokeMethod(self.detector, "cleanup", Qt.ConnectionType.QueuedConnection)
            if getattr(self, "detection_thread", None) and self.detection_thread.isRunning():
                # 2) Quitter la boucle une fois le timer nettoyé
                self.detection_thread.quit()
                self.detection_thread.wait(3000)
            # 3) Détruire le worker et le thread côté GUI (ils n'ont plus d'event loop)
            if getattr(self, "detector", None):
                self.detector.deleteLater()
                self.detector = None
            if getattr(self, "detection_thread", None):
                self.detection_thread.deleteLater()
                self.detection_thread = None
        except Exception:
            pass

        # Arrêt du thread de rafraîchissement si présent
        try:
            if (hasattr(self, 'current_refresh_thread') and 
                self.current_refresh_thread is not None and 
                self.current_refresh_thread.isRunning()):

                self.current_refresh_thread.quit()
                self.current_refresh_thread.wait(3000)  # Timeout 3 secondes
        except Exception:
            pass

        super().closeEvent(event)

class IconButton(QPushButton):
    def __init__(self, normal_icon, hover_icon, size=QSize(30, 30), parent=None):
        super().__init__(parent)
        self.normal_icon = QIcon(str(normal_icon))
        self.hover_icon = QIcon(str(hover_icon))
        self.setIcon(self.normal_icon)
        self.setIconSize(size)
        self.setFixedSize(size)
        self.setFlat(True)
        self.is_pressed = False

        self.pressed.connect(self.on_pressed)
        self.released.connect(self.on_released)

    def enterEvent(self, event):
        if not self.is_pressed:
            self.setIcon(self.hover_icon)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.is_pressed:
            self.setIcon(self.normal_icon)
        super().leaveEvent(event)

    def on_pressed(self):
        self.is_pressed = True
        self.setIcon(self.hover_icon)

    def on_released(self):
        self.is_pressed = False
        if self.underMouse():
            self.setIcon(self.hover_icon)
        else:
            self.setIcon(self.normal_icon)