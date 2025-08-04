# ui/enroll_widget.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import base64
import os


class EnrollWidget(QWidget):
    seed_enrolled = pyqtSignal()
    cancel_requested = pyqtSignal()
    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.setWindowTitle("Enroller une seed OTP")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # --- En-tête
        header = QHBoxLayout()
        back = QPushButton("←")
        back.setFixedWidth(30)
        back.clicked.connect(self.cancel_requested.emit)
        header.addWidget(back, 0, Qt.AlignmentFlag.AlignLeft)
        header.addStretch() # pousse le titre vers le centre
        title = QLabel("Ajouter un compte OTP")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch() # pousse le titre vers le centre
        header.addSpacing(back.width())  # même largeur que le bouton à gauche, pour que le titre soit bien centré visuellement
        layout.addLayout(header)

        # === Label du compte ===
        layout.addWidget(QLabel("Nom du compte :"))
        self.label_edit = QLineEdit("user@example.com")
        layout.addWidget(self.label_edit)

        # === Type OTP ===
        layout.addWidget(QLabel("Type OTP :"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["TOTP", "HOTP"])
        layout.addWidget(self.type_combo)

        # === Algo ===
        layout.addWidget(QLabel("Algorithme :"))
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["SHA1", "SHA256", "SHA512"])
        layout.addWidget(self.algo_combo)

        # === Longueur du code ===
        layout.addWidget(QLabel("Nombre de chiffres :"))
        self.digits_spin = QSpinBox()
        self.digits_spin.setRange(6, 8)
        self.digits_spin.setValue(6)
        layout.addWidget(self.digits_spin)

        # === Période ou compteur ===
        self.param_label = QLabel("Période (secondes) :")
        layout.addWidget(self.param_label)
        self.param_spin = QSpinBox()
        self.param_spin.setRange(0, 99999)
        self.param_spin.setValue(0)
        self.param_spin.hide()
        self.param_combo = QComboBox()
        self.param_combo.addItems(["30", "60"])
        layout.addWidget(self.param_combo)

        layout.addWidget(self.param_spin)

        self.type_combo.currentTextChanged.connect(self._update_param_label)

        # === Secret (seed) ===
        layout.addWidget(QLabel("Clé secrète (Base32) :"))
        seed_row = QHBoxLayout()
        self.seed_edit = QLineEdit()
        self.seed_edit.setPlaceholderText("JBSWY3DPEHPK3PXP...")
        seed_row.addWidget(self.seed_edit)
        gen_btn = QPushButton("🎲")
        gen_btn.setFixedWidth(40)
        gen_btn.setToolTip("Générer une seed aléatoire")
        gen_btn.clicked.connect(self._generate_seed)
        seed_row.addWidget(gen_btn)
        layout.addLayout(seed_row)

        # === Bouton Enroller ===
        enroll_btn = QPushButton("✅ Enroller")
        enroll_btn.clicked.connect(self._enroll)
        layout.addWidget(enroll_btn)

    def _update_param_label(self):
        if self.type_combo.currentText() == "TOTP":
            self.param_label.setText("Période (secondes) :")
            self.param_spin.hide()
            self.param_combo.show()
        else:
            self.param_label.setText("Compteur initial :")
            self.param_combo.hide()
            self.param_spin.show()

    def _generate_seed(self):
        length = {"SHA1": 20, "SHA256": 32, "SHA512": 64}
        algo = self.algo_combo.currentText()
        rand = os.urandom(length.get(algo, 20))
        self.seed_edit.setText(base64.b32encode(rand).decode("utf-8"))

    def _enroll(self):
        label = self.label_edit.text().strip()
        otp_type = self.type_combo.currentText()
        algo = self.algo_combo.currentText()
        digits = self.digits_spin.value()
        param = int(self.param_combo.currentText()) if otp_type == "TOTP" else int(self.param_spin.value())
        seed = self.seed_edit.text().strip().replace(" ", "")

        if not label or not seed:
            QMessageBox.warning(self, "Erreur", "Le label et la seed sont obligatoires.")
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
            error_msg = getattr(self.backend, "last_error", "Erreur inconnue")
            QMessageBox.critical(self, "Erreur OTP", error_msg)
