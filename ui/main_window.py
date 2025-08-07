# ui/main_window.py
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QScrollArea, QPushButton, QFrame, QMessageBox, QStackedLayout, QLineEdit
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QTimer, QSize, QThread
from ui.otp_card import OTPCard
from ui.enroll_widget import EnrollWidget
from core.fido_device import FidoOTPBackend
from core.otp_model import OTPGenerator
from core.otp_refresh_worker import OTPRefreshWorker

import time


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Winkeo/Badgeo OTP Manager")
        self.setWindowIcon(QIcon("images/logo.png"))
        self.resize(400, 600)

        self.backend = FidoOTPBackend()
        self.generator_widgets = {}
        self.worker_thread = None
        self.refresh_pending = False
        self.last_successful_refresh = 0
        self.device_connected = False

        #Pour une interface à onglets
        self.stack = QStackedLayout()
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self.stack)

        self.main_view = QWidget()
        main_view_layout = QVBoxLayout(self.main_view)
        self.stack.addWidget(self.main_view)

        # Header
        header_widget = QWidget()
        header_widget.setObjectName("header")
        header_layout = QHBoxLayout(header_widget)
        pixmap = QPixmap("images/logo.png")
        label_logo = QLabel()
        label_logo.setPixmap(pixmap.scaled(35, 35, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        label_logo.setScaledContents(False)
        label_titre = QLabel("NEOWAVE OTP MANAGER")
        label_titre.setObjectName("titreApp")
        header_layout.addStretch()
        header_layout.addWidget(label_logo)
        header_layout.addWidget(label_titre)
        header_layout.addStretch()        
        main_view_layout.addWidget(header_widget)

        header_layout.setContentsMargins(0, 15, 0, 15)
        header_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_view_layout.setContentsMargins(0, 0, 0, 0)
        main_view_layout.setSpacing(0)

        # boutton enrol et searchbar
        enrol_search_widget = QWidget()
        enrol_search_widget.setObjectName("enrolSeach")
        enrol_search_layout = QHBoxLayout(enrol_search_widget)

        enrol_button = IconButton("images/plus5.png", "images/plus_clicked.png")

        search_bar = QLineEdit()
        search_bar.setObjectName("searchBar")
        search_bar.setPlaceholderText("Rechercher un code...")
        search_bar.setClearButtonEnabled(True)
        search_bar.textChanged.connect(self.on_search_text_changed)
        search_bar.setMinimumWidth(250)
        enrol_search_layout.addWidget(enrol_button, alignment=Qt.AlignmentFlag.AlignLeft)
        enrol_search_layout.addStretch()
        enrol_search_layout.addWidget(search_bar)
        enrol_search_layout.addStretch()
        enrol_button.clicked.connect(self.switch_to_enroll_view)
        main_view_layout.addWidget(enrol_search_widget)

        # OTP list area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.otp_list_widget = QWidget()
        self.otp_list_widget.setObjectName("listArea")
        self.otp_list_layout = QVBoxLayout(self.otp_list_widget)
        self.otp_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area.setWidget(self.otp_list_widget)
        main_view_layout.addWidget(scroll_area, stretch=1)

        #Status présence du device
        self.status_label = QLabel()
        self.status_label.setObjectName("statusKey")
        self.status_label.hide()
        main_view_layout.addWidget(self.status_label)

        # === Vue d'enrôlement ===
        self.enroll_widget = EnrollWidget(self.backend, self)
        self.enroll_widget.seed_enrolled.connect(self.on_enroll_success)
        self.enroll_widget.cancel_requested.connect(self.switch_to_main_view)
        self.stack.addWidget(self.enroll_widget)

        # Timer principal - moins fréquent pour réduire la charge
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.schedule_refresh)
        self.timer.start(500)  # 0.5s

        # Timer pour les barres de progression TOTP
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress_bars)
        self.progress_timer.start(50)

        # Première tentative de connexion
        self.schedule_refresh()

    def update_progress_bars(self):
        """Met à jour les barres de progression et déclenche un refresh si nécessaire"""
        now = time.time()

        for card in self.generator_widgets.values():
            if card.otp_type == 2:  # TOTP seulement
                card.update_progress_value(now)

        
    def on_search_text_changed(self, text):
        for label, card in self.generator_widgets.items():
            card.setVisible(text.lower() in label.lower())

    def switch_to_enroll_view(self):
        if not self.device_connected:
            QMessageBox.warning(self, "Erreur", "Aucun périphérique OTP détecté. Veuillez connecter votre clé.")
            return
        self.stack.setCurrentWidget(self.enroll_widget)

    def switch_to_main_view(self):
        self.stack.setCurrentWidget(self.main_view)

    def on_enroll_success(self):
        self.schedule_refresh(force=True)
        self.switch_to_main_view()

    def schedule_refresh(self, force=False):
        """Planifie un refresh en évitant les doublons"""

        if self.refresh_pending:
            return
            
        if hasattr(self, 'worker_thread') and self.worker_thread is not None and self.worker_thread.isRunning():
            return
            
        self.refresh_pending = True
        self.start_refresh_thread()

    def start_refresh_thread(self):
        """Lance le worker dans un thread séparé"""
        self.worker_thread = QThread()
        self.worker = OTPRefreshWorker(self.backend)
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_refresh_data_ready)
        self.worker.error.connect(self.on_refresh_error)
        self.worker.device_status_changed.connect(self.on_device_status_changed)
        
        # Nettoyage
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker_thread.quit)
        self.worker.error.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(lambda: setattr(self, 'worker_thread', None))
        self.worker_thread.finished.connect(self.on_worker_finished)
        
        self.worker_thread.start()

    def on_worker_finished(self):
        """Appelé quand le worker se termine"""
        self.refresh_pending = False

    def on_device_status_changed(self, connected):
        """Gère les changements d'état de connexion du device"""
        if connected != self.device_connected:
            self.device_connected = connected
            if connected:
                self.status_label.hide()
                # Device reconnecté - forcer un refresh immédiat
                QTimer.singleShot(100, lambda: self.schedule_refresh(force=True))
            else:
                self.clear_all_cards()
                self.status_label.setText("🔌 Aucun périphérique OTP détecté.")
                self.status_label.show()

    def on_refresh_data_ready(self, generators):
        """Met à jour l'UI avec les nouvelles données"""
        self.last_successful_refresh = time.time()
        self.device_connected = True
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
                card.request_code.connect(lambda l=g.label, t=g.otp_type, p=g.period: self.generate_and_update(l, t, p))
                card.delete_requested.connect(self.confirm_delete)
                self.otp_list_layout.addWidget(card)
                self.generator_widgets[label] = card
            else:
                # Mettre à jour le code seulement pour TOTP
                if g.otp_type == 2:  # TOTP
                    self.generator_widgets[label].set_code(g.code)
                # Pour HOTP, ne pas mettre à jour automatiquement

        # Supprimer les cartes qui n'existent plus
        for old_label in existing - active:
            card = self.generator_widgets.pop(old_label)
            card.setParent(None)

    def on_refresh_error(self, message):
        """Gère les erreurs de refresh"""
        self.device_connected = False
        self.status_label.setText(f"❌ Erreur : {message}")
        self.status_label.show()
        
        # Ne pas vider les cartes immédiatement - laisser une chance de reconnexion
        # self.clear_all_cards()

    def clear_all_cards(self):
        """Vide toutes les cartes OTP"""
        for card in self.generator_widgets.values():
            card.setParent(None)
        self.generator_widgets.clear()

    def generate_and_update(self, label, otp_type, period):
        """Génère et met à jour un code spécifique (pour HOTP principalement)"""
        if not self.device_connected:
            return
            
        # Pour HOTP, on fait un appel direct et rapide
        code = self.backend.generate_code(label, otp_type, period)
        if code is None:
            code = f"Err: {getattr(self.backend, 'last_error', 'inconnue')}"
        
        if label in self.generator_widgets:
            self.generator_widgets[label].set_code(code)

    def confirm_delete(self, label):
        if not self.device_connected:
            QMessageBox.warning(self, "Erreur", "Aucun périphérique OTP détecté.")
            return
            
        reply = QMessageBox.question(
            self,
            f"Supprimer {label}",
            f"Confirmer la suppression du générateur OTP '{label}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = self.backend.delete_generator(label)
            if success:
                # Forcer un refresh pour mettre à jour la liste
                self.schedule_refresh(force=True)
            else:
                error_msg = getattr(self.backend, "last_error", f"Échec de la suppression de '{label}'")
                QMessageBox.warning(self, "Erreur", error_msg)

    def closeEvent(self, event):
        """Nettoyage à la fermeture"""
        try:
            if hasattr(self, 'worker_thread') and self.worker_thread and self.worker_thread.isRunning():
                self.worker_thread.quit()
                self.worker_thread.wait(3000)  # Timeout de 3 secondes
        except Exception:
            pass
        super().closeEvent(event)


class IconButton(QPushButton):
    def __init__(self, normal_icon, hover_icon, parent=None):
        super().__init__(parent)
        self.normal_icon = QIcon(normal_icon)
        self.hover_icon = QIcon(hover_icon)
        self.setIcon(self.normal_icon)
        self.setIconSize(QSize(30, 30))
        self.setFixedSize(30, 30)
        self.setFlat(True)
        self.setObjectName("enrolButton")
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