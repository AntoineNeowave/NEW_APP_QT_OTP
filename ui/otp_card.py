# ui/otp_card.py
# Affiche un compte OTP sous forme de carte avec le code, le label et les paramètres.
from PyQt6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar,
    QMenu, QMessageBox, QApplication, QWidget
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from ui.progress_indicator import ProgressIndicator

class OTPCard(QFrame):
    request_code = pyqtSignal(str)  # signal avec le label
    delete_requested = pyqtSignal(str)
    parameters_requested = pyqtSignal(str, int) #label, otp_type

    def __init__(self, label: str, code: str, parameters: str, otp_type: int, period: int, parent=None):
        super().__init__(parent)
        if ":" in label:
            self.account, self.issuer = label.split(":", 1)
        else:
            self.account = label
            self.issuer = ""
        self.label_text = label
        self.otp_type = otp_type
        self.period = period
        self.remaining_seconds = 0
        self.parameter_text = parameters

        self.setObjectName("otpCard")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5) # marge autour de la carte
        #main_layout.setSpacing(0) # espace entre les widgets à l'intérieur de la carte
        # Labels
        left_widget = QWidget()
        left_widget.setFixedWidth(200)
        left_layout = QVBoxLayout(left_widget)
        self.label_code = QLabel(f"{code}")
        self.label_code.setObjectName("codeLabel")
        self.label_code.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        code_layout = QHBoxLayout()
        code_layout.addWidget(self.label_code)
        copy_button = QPushButton(QIcon("images/copier.png"), "")
        copy_button.setFixedSize(24, 24)
        copy_button.setFlat(True)
        copy_button.setToolTip("Copy code to clipboard")
        copy_button.clicked.connect(lambda: 
            QApplication.clipboard().setText(self.label_code.text()),
        )
        code_layout.addWidget(copy_button)
        code_layout.addStretch()
        self.account_label = QLabel(f"{self.account}")
        self.account_label.setObjectName("accountName")
        self.issuer_label = QLabel(f"{self.issuer}")
        self.issuer_label.setObjectName("issuer")
        left_layout.addWidget(self.account_label)
        left_layout.addWidget(self.issuer_label)
        left_layout.addLayout(code_layout)

        main_layout.addWidget(left_widget)
        main_layout.addStretch()
        self.btn = QPushButton()
        if otp_type == 1:  # HOTP
            self.btn.setIcon(QIcon("images/refresh.png"))
            self.btn.setIconSize(QSize(27, 27))
            self.btn.setFixedSize(27, 27)
            self.btn.setFlat(True)
            self.btn.clicked.connect(lambda: self.request_code.emit(self.label_text))
            main_layout.addWidget(self.btn)
        else:  # TOTP
            self.progress = ProgressIndicator(period)
            main_layout.addWidget(self.progress, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        main_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

    def set_code(self, code: str):
        self.label_code.setText(f"{code}")

    def update_progress_value(self, current_time):
        """Met à jour la barre de progression pour TOTP"""
        if self.otp_type == 2:  # TOTP seulement
            self.progress.update_progress_value(current_time)
            self.remaining_seconds = self.progress.remaining_seconds

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        show_params_action = QAction("Show parameters", self)
        show_params_action.triggered.connect(lambda: self.parameters_requested.emit(self.label_text, self.otp_type))

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.label_text))

        menu.addAction(show_params_action)
        menu.addAction(delete_action)
        menu.exec(event.globalPos())

    def show_parameters(self):
        msg = QMessageBox(self)
        msg.setWindowTitle(f"Parameters - {self.account}")
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        msg.setText(self.parameter_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()


    def set_offline(self, reason: str = "Disconnected"):
        # Affiche un code neutre et un sous-titre explicite
        self.label_code.setText("●●●●●●")
        self.account.setText(reason)
        self.issuer.setText("")
        if self.otp_type == 2:
            self.progress.setVisible(False)
        else:
            self.btn.setVisible(False)
        self.setProperty("offline", True)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_online(self):
        self.setProperty("offline", False)
        self.account_label.setText(self.account)
        self.issuer_label.setText(self.issuer)
        if self.otp_type == 2:
            self.progress.setVisible(True)
        else:
            self.btn.setVisible(True)
        self.style().unpolish(self)
        self.style().polish(self)