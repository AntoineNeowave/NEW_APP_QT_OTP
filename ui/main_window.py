# ui/main_window.py
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QScrollArea, QPushButton, QFrame
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer
from ui.otp_card import OTPCard
from core.fido_device import FidoOTPBackend
from core.otp_model import OTPGenerator

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestionnaire OTP Winkeo/Badgeo")
        self.resize(400, 600)

        self.backend = FidoOTPBackend()
        self.generator_widgets = {}

        main_layout = QVBoxLayout(self)

        # Header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        pixmap = QPixmap("images/logo.png")
        label_logo = QLabel()
        label_logo.setPixmap(pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio))
        label_logo.setFixedSize(80, 80)
        label_titre = QLabel("NEOWAVE OTP MANAGER")
        header_layout.addWidget(label_titre)
        header_layout.addStretch()
        header_layout.addWidget(label_logo)
        main_layout.addWidget(header_widget)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)

        # OTP list area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.otp_list_widget = QWidget()
        self.otp_list_layout = QVBoxLayout(self.otp_list_widget)
        scroll_area.setWidget(self.otp_list_widget)
        main_layout.addWidget(scroll_area, stretch=1)

        # Footer
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        enrol_button = QPushButton("➕ Enroller une seed")
        info_label = QLabel("Mentions légales | Contact")
        footer_layout.addWidget(enrol_button)
        footer_layout.addStretch()
        footer_layout.addWidget(info_label)
        main_layout.addWidget(footer)

        self.refresh()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

    def refresh(self):
        raw_generators = self.backend.list_generators()
        generators = [OTPGenerator(g) for g in raw_generators]

        existing = set(self.generator_widgets.keys())
        active = set()

        for g in generators:
            label = g.label
            active.add(label)

            if label not in self.generator_widgets:
                card = OTPCard(
                    label=g.label,
                    code="...",
                    subtitle=g.display_subtitle(),
                    otp_type=g.otp_type
                )
                card.request_code.connect(lambda l=g.label, t=g.otp_type, p=g.period: self.generate_and_update(l, t, p))
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
        self.generator_widgets[label].set_code(code)