# ui/main_window.py
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QScrollArea, QPushButton, QFrame, QMessageBox, QStackedLayout, QLineEdit
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QTimer, QSize
from ui.otp_card import OTPCard
from ui.enroll_widget import EnrollWidget
from core.fido_device import FidoOTPBackend
from core.otp_model import OTPGenerator
import time
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Winkeo/Badgeo OTP Manager")
        self.setWindowIcon(QIcon("images/logo.png"))
        self.resize(400, 600)

        self.backend = FidoOTPBackend()
        self.generator_widgets = {}

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
        # label_logo.setFixedSize(30, 30)
        label_logo.setPixmap(pixmap.scaled(35, 35, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        label_logo.setScaledContents(False)
        label_titre = QLabel("NEOWAVE OTP MANAGER")
        label_titre.setObjectName("titreApp")
        header_layout.addStretch()
        header_layout.addWidget(label_logo)
        header_layout.addWidget(label_titre)
        header_layout.addStretch()        
        main_view_layout.addWidget(header_widget)

        header_layout.setContentsMargins(0, 15, 0, 15)  # supprime marges du layout
        header_layout.setSpacing(0)  # réduit espacement entre widgets
        main_layout.setContentsMargins(0, 0, 0, 0)  # ou (0,0,0,0) pour tout supprimer
        main_layout.setSpacing(0)
        main_view_layout.setContentsMargins(0, 0, 0, 0)
        main_view_layout.setSpacing(0)

        # boutton enrol et searchbar
        enrol_search_widget  = QWidget()
        enrol_search_widget.setObjectName("enrolSeach")
        enrol_search_layout  = QHBoxLayout(enrol_search_widget )
        # enrol_layout.setContentsMargins(0,0,0,0)
        # enrol_layout.setSpacing(0)

        enrol_button = IconButton("images/plus5.png", "images/plus_clicked.png")


        search_bar = QLineEdit()
        search_bar.setObjectName("searchBar")
        search_bar.setPlaceholderText("Rechercher un code...")
        search_bar.setClearButtonEnabled(True)
        search_bar.textChanged.connect(self.on_search_text_changed)
        search_bar.setMinimumWidth(250)
        enrol_search_layout .addWidget(enrol_button, alignment=Qt.AlignmentFlag.AlignLeft)
        enrol_search_layout.addStretch()
        enrol_search_layout .addWidget(search_bar)
        enrol_search_layout.addStretch()
        enrol_button.clicked.connect(self.switch_to_enroll_view)
        main_view_layout.addWidget(enrol_search_widget )

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

        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress_bars)
        self.progress_timer.start(50)

    def update_progress_bars(self):
        now = time.time()
        for card in self.generator_widgets.values():
            if card.otp_type == 2:
                card.update_progress_value(now)

        
    def on_search_text_changed(self, text):
        # parcourir cards, cacher ceux qui ne correspondent pas
        for label, card in self.generator_widgets.items():
            card.setVisible(text.lower() in label.lower())

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
                #card.setMaximumHeight(100)
                self.generator_widgets[label] = card


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
        # Survol souris
        if not self.is_pressed:
            self.setIcon(self.hover_icon)
        super().enterEvent(event)

    def leaveEvent(self, event):
        # Quitte bouton
        if not self.is_pressed:
            self.setIcon(self.normal_icon)
        super().leaveEvent(event)

    def on_pressed(self):
        self.is_pressed = True
        self.setIcon(self.hover_icon)

    def on_released(self):
        self.is_pressed = False
        # Remet l’icône en fonction de l’état hover/survol
        if self.underMouse():
            self.setIcon(self.hover_icon)
        else:
            self.setIcon(self.normal_icon)