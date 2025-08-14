# ui/enroll_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QSpinBox, QMessageBox,QToolButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QSize
import base64
import os
from PyQt6.QtGui import QPixmap, QIcon
from ui.header import Header
from PyQt6.QtGui import QValidator, QIcon

class EnrollWidget(QWidget):
    seed_enrolled = pyqtSignal()
    cancel_requested = pyqtSignal()
    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.setWindowTitle("Enroll OTP secret")
        self.setMinimumWidth(400)

        enroll_view_layout = QVBoxLayout(self)
        enroll_view_layout.setContentsMargins(0, 0, 0, 0)
        enroll_view_layout.setSpacing(0)

        # --- En-tête
        header_widget = Header()
        enroll_view_layout.addWidget(header_widget)
        
        page_header_widget = QWidget()
        page_header_widget.setObjectName("enrollHeader")
        page_header_layout = QHBoxLayout(page_header_widget)
        from ui.main_window import IconButton
        back = IconButton("images/left-arrow.png", "images/left-arrow-clicked.png")
        back.setObjectName("returnButton")
        back.clicked.connect(self.cancel_requested.emit)
        page_header_layout.addWidget(back, 0, Qt.AlignmentFlag.AlignLeft)
        page_header_layout.addStretch() # pousse le titre vers le centre
        title = QLabel("Add OTP Account")
        title.setObjectName("enrollTitle")
        page_header_layout.addWidget(title)
        page_header_layout.addStretch() # pousse le titre vers le centre
        page_header_layout.addSpacing(back.width())  # même largeur que le bouton à gauche, pour que le titre soit bien centré visuellement
        enroll_view_layout.addWidget(page_header_widget)

        # Contenu principal avec marges
        content_widget = QWidget()
        content_widget.setObjectName("enrollPanel")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)  # Marges autour du contenu
        content_layout.setSpacing(20)  # Espacement entre les éléments
        
        enroll_view_layout.addWidget(content_widget)
        
        no_colon_validator = NoColonValidator()

        # === Nom du compte ===
        account_section = QWidget()
        account_layout = QVBoxLayout(account_section)
        account_layout.setContentsMargins(0, 0, 0, 0)
        account_layout.setSpacing(4)
        account_name = QLabel("Account name <span style='color:red'>*</span> :")
        account_layout.addWidget(account_name)
        self.account_edit = QLineEdit()
        self.account_edit.setPlaceholderText("Google, GitHub, etc.")
        self.account_edit.setValidator(no_colon_validator)
        self.account_edit.textChanged.connect(self._field_changed)
        account_layout.addWidget(self.account_edit)
        self.account_edit.setToolTip("Account name should not contain ':'")
        content_layout.addWidget(account_section)

        # === Issuer du compte ===
        issuer_section = QWidget()
        issuer_layout = QVBoxLayout(issuer_section)
        issuer_layout.setContentsMargins(0, 0, 0, 0)
        issuer_layout.setSpacing(4)
        issuer_name = QLabel("Issuer name :")
        issuer_layout.addWidget(issuer_name)
        self.issuer_edit = QLineEdit()
        self.issuer_edit.setPlaceholderText("user@example.com")
        self.issuer_edit.setValidator(no_colon_validator)
        self.issuer_edit.setToolTip("Issuer name should not contain ':'")
        issuer_layout.addWidget(self.issuer_edit)
        content_layout.addWidget(issuer_section)

        # === Secret (seed) ===
        seed_section = QWidget()
        seed_layout = QVBoxLayout(seed_section)
        seed_layout.setContentsMargins(0, 0, 0, 0)
        seed_layout.setSpacing(4)
        seed_label = QLabel("Secret key (Base32) <span style='color:red'>*</span> :")
        seed_layout.addWidget(seed_label)
        seed_row = QHBoxLayout()
        self.seed_edit = QLineEdit()
        self.seed_edit.setPlaceholderText("JBSWY3DPEHPK3PXP...")
        self.seed_edit.textChanged.connect(self._field_changed)
        seed_row.addWidget(self.seed_edit)
        from ui.main_window import IconButton
        gen_btn = IconButton("images/generate.png", "images/generate_clicked.png", QSize(24, 24))
        gen_btn.setToolTip("Generate a random seed")
        gen_btn.clicked.connect(self._generate_seed)
        seed_row.addWidget(gen_btn)
        seed_layout.addLayout(seed_row)
        content_layout.addWidget(seed_section)

        content_layout.addSpacing(5)

        # === Bouton pour afficher/masquer les paramètres ===
        self.show_params_btn = QToolButton()
        self.show_params_btn.setText("Advanced options")
        self.show_params_btn.setObjectName("advancedOptionsBtn")
        self.show_params_btn.setCheckable(True)

        self.icon_down = QIcon("images/down-arrow.png")
        self.icon_down_dark = QIcon("images/down-arrow-dark.png")
        self.icon_up_dark = QIcon("images/up-arrow-dark.png")
        self.show_params_btn.setIcon(self.icon_down)
        self.show_params_btn.installEventFilter(self)
        self.show_params_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.show_params_btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.show_params_btn.clicked.connect(self._toggle_parameters_visibility)
        content_layout.addWidget(self.show_params_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.parameters_panel = QWidget()
        self.parameters_panel.setObjectName("parametersPanel")
        self.parameters_panel.hide()

        params_layout = QHBoxLayout(self.parameters_panel)
        params_layout.setSpacing(15)
        #params_layout.setContentsMargins(0, 0, 0, 0)

        # === Type OTP ===
        type_section = QWidget()
        type_layout = QVBoxLayout(type_section)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.setSpacing(4)
        type_label = QLabel("OTP Type :")
        type_label.setWordWrap(True)
        type_layout.addWidget(type_label)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["TOTP", "HOTP"])
        type_layout.addWidget(self.type_combo)
        params_layout.addWidget(type_section)

        # === Algo ===
        algo_section = QWidget()
        algo_layout = QVBoxLayout(algo_section)
        algo_layout.setContentsMargins(0, 0, 0, 0)
        algo_layout.setSpacing(4)
        algo_label = QLabel("Algorithm :")
        algo_label.setWordWrap(True)
        algo_layout.addWidget(algo_label)
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["SHA1", "SHA256", "SHA512"])
        algo_layout.addWidget(self.algo_combo)
        params_layout.addWidget(algo_section)

        # === Longueur du code ===
        digits_section = QWidget()
        digits_layout = QVBoxLayout(digits_section)
        digits_layout.setContentsMargins(0, 0, 0, 0)
        digits_layout.setSpacing(4)
        digits_label = QLabel("Number of digits :")
        digits_label.setWordWrap(True)
        digits_layout.addWidget(digits_label)
        self.digits_spin = QSpinBox()
        self.digits_spin.setRange(6, 8)
        self.digits_spin.setValue(6)
        digits_layout.addWidget(self.digits_spin)
        params_layout.addWidget(digits_section)

        # === Période ou compteur ===
        period_counter_section = QWidget()
        period_counter_layout = QVBoxLayout(period_counter_section)
        period_counter_layout.setContentsMargins(0, 0, 0, 0)
        period_counter_layout.setSpacing(4)
        self.param_label = QLabel("Timestep (seconds) :")
        self.param_label.setWordWrap(True)
        period_counter_layout.addWidget(self.param_label)
        self.counter_spin = QSpinBox()
        self.counter_spin.setRange(0, 99999)
        self.counter_spin.setValue(0)
        self.counter_spin.hide()
        self.period_combo = QComboBox()
        self.period_combo.addItems(["30", "60"])
        period_counter_layout.addWidget(self.period_combo)
        period_counter_layout.addWidget(self.counter_spin)
        params_layout.addWidget(period_counter_section)

        self.type_combo.currentTextChanged.connect(self._update_param_label)
        content_layout.addWidget(self.parameters_panel)

        # === Bouton Enroller ===
        enroll_btn = QPushButton("Add account")
        enroll_btn.setObjectName("enrollBtn")
        enroll_btn.clicked.connect(self._enroll)
        content_layout.addWidget(enroll_btn)

        content_layout.addStretch()

    def _field_changed(self, text):
        widget = self.sender()  
        if text.strip():
            widget.setStyleSheet("")

    def _toggle_parameters_visibility(self):
        if self.parameters_panel.isHidden():
            self.parameters_panel.show()
            self.show_params_btn.setIcon(self.icon_up_dark)
        else:
            self.parameters_panel.hide()
            # Après avoir décoché, on vérifie si la souris est toujours sur le bouton
            if self.show_params_btn.underMouse():
                self.show_params_btn.setIcon(self.icon_down_dark)
            else:
                self.show_params_btn.setIcon(self.icon_down)

    def eventFilter(self, obj, event):
        if obj is self.show_params_btn:
            if event.type() == QEvent.Type.Enter:
                # Si le bouton n'est pas coché, on met l'icône de survol
                if not self.show_params_btn.isChecked():
                    self.show_params_btn.setIcon(self.icon_down_dark)
            elif event.type() == QEvent.Type.Leave:
                # Si le bouton n'est pas coché, on remet l'icône de base
                if not self.show_params_btn.isChecked():
                    self.show_params_btn.setIcon(self.icon_down)
        return super().eventFilter(obj, event)

    def _update_param_label(self):
        if self.type_combo.currentText() == "TOTP":
            self.param_label.setText("Timestep (seconds) :")
            self.counter_spin.hide()
            self.period_combo.show()
        else:
            self.param_label.setText("Initial counter :")
            self.period_combo.hide()
            self.counter_spin.show()

    def _generate_seed(self):
        length = {"SHA1": 20, "SHA256": 32, "SHA512": 64}
        algo = self.algo_combo.currentText()
        rand = os.urandom(length.get(algo, 20))
        self.seed_edit.setText(base64.b32encode(rand).decode("utf-8"))

    def is_base32(s: str) -> bool:
        try:
            # Essaye de décoder la chaîne (en bytes)
            base64.b32decode(s.upper(), casefold=True)  
            return True
        except Exception:
            # Si une erreur est levée, ce n'est pas du Base32 valide
            return False
    
    def _enroll(self):
        account_name = self.account_edit.text().strip()
        issuer_name = self.issuer_edit.text().strip()
        label = f"{account_name}:{issuer_name}" if issuer_name else account_name
        otp_type = self.type_combo.currentText()
        algo = self.algo_combo.currentText()
        digits = self.digits_spin.value()
        param = int(self.period_combo.currentText()) if otp_type == "TOTP" else int(self.counter_spin.value())
        seed = self.seed_edit.text().strip().replace(" ", "")

        if not label :
            QMessageBox.warning(self, "Error", "Account name is required.")
            self.account_edit.setStyleSheet("background-color: #ffe4e1;")
            return
        if not seed:
            QMessageBox.warning(self, "Error", "Secret key is required.")
            self.seed_edit.setStyleSheet("background-color: #ffe4e1;")
            return
        if seed and not EnrollWidget.is_base32(seed):
            QMessageBox.warning(self, "Error", "Secret key must be a valid Base32 string.")
            self.seed_edit.setStyleSheet("background-color: #ffe4e1;")
            return

        success = self.backend.create_generator(
            label=label,
            otp_type=otp_type,
            secret_b32=seed,
            algo=algo,
            digits=digits,
            counter=param if otp_type == "HOTP" else None,
            period=param if otp_type == "TOTP" else None
        )

        if success:
            self.seed_enrolled.emit()

        else:
            error_msg = getattr(self.backend, "last_error", "Unknown error")
            QMessageBox.critical(self, "OTP Error", error_msg)

class NoColonValidator(QValidator):
    def validate(self, input_str, pos):
        if ':' in input_str:
            return (QValidator.State.Invalid, input_str, pos)
        return (QValidator.State.Acceptable, input_str, pos)