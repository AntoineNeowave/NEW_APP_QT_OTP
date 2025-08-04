# ui/main_window.py
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QScrollArea, QPushButton, QFrame, QMessageBox, QStackedLayout
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer
from ui.otp_card import OTPCard
from ui.enroll_widget import EnrollWidget
from core.fido_device import FidoOTPBackend
from core.otp_model import OTPGenerator

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestionnaire OTP Winkeo/Badgeo")
        self.resize(400, 600)

        self.backend = FidoOTPBackend()
        self.generator_widgets = {}

        self.stack = QStackedLayout()
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self.stack)

        self.main_view = QWidget()
        main_view_layout = QVBoxLayout(self.main_view)
        self.stack.addWidget(self.main_view)

        # Header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        pixmap = QPixmap("images/logo.png")
        label_logo = QLabel()
        label_logo.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        label_logo.setFixedSize(label_logo.pixmap().size())
        label_titre = QLabel("NEOWAVE OTP MANAGER")
        header_layout.addWidget(label_titre)
        header_layout.addStretch()
        header_layout.addWidget(label_logo)        
        main_view_layout.addWidget(header_widget)

        # header_layout.setContentsMargins(0, 0, 0, 0)  # supprime marges du layout
        # header_layout.setSpacing(0)  # réduit espacement entre widgets
        # label_logo.setContentsMargins(0, 0, 0, 0)   # supprime marges internes logo
        # label_titre.setContentsMargins(0, 0, 0, 0)  # supprime marges internes titre
        # main_layout.setContentsMargins(0, 0, 0, 0)  # ou (0,0,0,0) pour tout supprimer
        # main_layout.setSpacing(0)


        # OTP list area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.otp_list_widget = QWidget()
        self.otp_list_layout = QVBoxLayout(self.otp_list_widget)
        scroll_area.setWidget(self.otp_list_widget)
        main_view_layout.addWidget(scroll_area, stretch=1)


        # Footer
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        enrol_button = QPushButton("➕ Enroller une seed")
        info_label = QLabel("Mentions légales | Contact")
        footer_layout.addWidget(enrol_button)
        footer_layout.addStretch()
        footer_layout.addWidget(info_label)
        enrol_button.clicked.connect(self.switch_to_enroll_view)
        main_view_layout.addWidget(footer)

        #Status présence du device
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: red; font-style: italic;")
        self.status_label.hide()  # caché par défaut
        main_view_layout.addWidget(self.status_label)

        # === Vue d’enrôlement ===
        self.enroll_widget = EnrollWidget(self.backend, self)
        self.enroll_widget.seed_enrolled.connect(self.on_enroll_success)
        self.enroll_widget.cancel_requested.connect(self.switch_to_main_view)
        self.stack.addWidget(self.enroll_widget)

        self.refresh()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)
    
    def switch_to_enroll_view(self):
        self.stack.setCurrentWidget(self.enroll_widget)

    def switch_to_main_view(self):
        self.stack.setCurrentWidget(self.main_view)

    def on_enroll_success(self):
        self.refresh()
        self.switch_to_main_view()

    def refresh(self):
        raw_generators = self.backend.list_generators()
        if not raw_generators:
            self.status_label.setText("🔌 Aucun périphérique OTP détecté.")
            self.status_label.show()
            return
        else:
            self.status_label.hide()
        generators = [OTPGenerator(g) for g in raw_generators]

        existing = set(self.generator_widgets.keys())
        active = set()

        for g in generators:
            label = g.label
            active.add(label)

            if label not in self.generator_widgets:
                code = self.backend.generate_code(label, g.otp_type, g.period)

                if code is None:
                    code = "Erreur"

                card = OTPCard(
                    label=g.label,
                    code=code,
                    parameters=g.display_parameters(),
                    otp_type=g.otp_type,
                    period=g.period
                )
                card.request_code.connect(lambda l=g.label, t=g.otp_type, p=g.period: self.generate_and_update(l, t, p))
                card.delete_requested.connect(self.confirm_delete)
                self.otp_list_layout.addWidget(card)
                self.generator_widgets[label] = card

            if g.otp_type == 2:
                self.generator_widgets[label].update_progress(g.period)

        for old_label in existing - active:
            card = self.generator_widgets.pop(old_label)
            card.setParent(None)

        for label, card in self.generator_widgets.items():
            if card.otp_type == 2 and card.remaining_seconds == 0:
                self.generate_and_update(label, 2, card.period)

    def generate_and_update(self, label, otp_type, period):
        code = self.backend.generate_code(label, otp_type, period)
        if code is None:
            code = f"Err: {getattr(self.backend, 'last_error', 'inconnue')}"
        self.generator_widgets[label].set_code(code)

    def confirm_delete(self, label):
        reply = QMessageBox.question(
            self,
            f"Supprimer {label}",
            f"Confirmer la suppression du générateur OTP '{label}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = self.backend.delete_generator(label)
            if success:
                card = self.generator_widgets.pop(label)
                card.setParent(None)
            else:
                error_msg = getattr(self.backend, "last_error", f"Échec de la suppression de '{label}'")
                QMessageBox.warning(self, "Erreur", error_msg)