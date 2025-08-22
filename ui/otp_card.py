# ui/otp_card.py
# Affiche un compte OTP sous forme de carte avec le code, le label et les paramètres.
from PyQt6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QMenu, QMessageBox, QApplication, QWidget
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from ui.progress_indicator import ProgressIndicator
from ui.ressources import resource_path

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
        self.code = code

        self.setObjectName("otpCard")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 15, 5) # marge autour de la carte
        #main_layout.setSpacing(0) # espace entre les widgets à l'intérieur de la carte
        # Labels
        left_widget = QWidget()
        left_widget.setFixedWidth(200)
        left_layout = QVBoxLayout(left_widget)
        self.label_code = QLabel()
        self.label_code.setObjectName("codeLabel")
        self.label_code.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        code_layout = QHBoxLayout()
        code_layout.addWidget(self.label_code)
        copy_button_path = resource_path("images/copy.png")
        copy_button_clicked_path = resource_path("images/copy_clicked.png")
        self.copy_button = QPushButton()
        from ui.main_window import IconButton
        self.copy_button = IconButton(copy_button_path, copy_button_clicked_path, QSize(16, 16))
        self.copy_button.setFixedSize(16, 16)
        self.copy_button.setFlat(True)
        self.copy_button.setToolTip("Copy code to clipboard")
        self.copy_button.setVisible(False)
        self.feedback_label = QLabel("Code copied")
        self.feedback_label.setObjectName("CopiedLabel")
        self.feedback_label.setVisible(False)
        self.copy_button.clicked.connect(self.copy_code)
        code_layout.addWidget(self.copy_button)
        code_layout.addWidget(self.feedback_label)
        code_layout.addStretch()
        self.account_label = QLabel(f"{self.account}")
        self.account_label.setObjectName("accountName")
        self.account_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.issuer_label = QLabel(f"{self.issuer}")
        self.issuer_label.setObjectName("issuer")
        self.issuer_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        left_layout.addWidget(self.account_label)
        left_layout.addWidget(self.issuer_label)
        left_layout.addLayout(code_layout)

        main_layout.addWidget(left_widget)
        main_layout.addStretch()
        self.btn = QPushButton()
        if otp_type == 1:  # HOTP
            refresh_icon_path = resource_path("images/refresh.png")
            refresh_icon_clicked_path = resource_path("images/refresh_clicked.png")
            self.btn = IconButton(refresh_icon_path, refresh_icon_clicked_path, QSize(35, 35))
            self.btn.setFlat(True)
            self.btn.clicked.connect(lambda: self.request_code.emit(self.label_text))
            main_layout.addWidget(self.btn)
        else:  # TOTP
            self.progress = ProgressIndicator(period)
            main_layout.addWidget(self.progress)
        
        main_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.set_code(self.code)

    def format_code(self, code):
        code = str(code)
        if len(code) == 6:
            return code[:3] + " " + code[3:]
        elif len(code) == 7:
            return code[:4] + " " + code[4:]
        elif len(code) == 8:
            return code[:4] + " " + code[4:]
        else:
            return code  # on retourne le code tel quel pour les autres tailles

    def copy_code(self):
        code_with_spaces = self.label_code.text()
        code_without_spaces = code_with_spaces.replace(" ", "")
        QApplication.clipboard().setText(code_without_spaces)
        # afficher "Code copied"
        self.feedback_label.setVisible(True)
        # cacher après 1 sec
        QTimer.singleShot(1000, lambda: self.feedback_label.setVisible(False))

    def set_code(self, code: str):
        if "●" in code:
            self.label_code.setText(code)
            self.copy_button.setVisible(False)
        else:
            formatted_code = self.format_code(code)
            self.label_code.setText(formatted_code)
            self.copy_button.setVisible(True)

    def update_progress_value(self, current_time):
        """Met à jour la barre de progression pour TOTP"""
        if self.otp_type == 2:  # TOTP seulement
            self.progress.update_progress_value(current_time)
            self.remaining_seconds = self.progress.remaining_seconds

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        show_params_action = QAction("Show OTP parameters", self)
        show_params_action.triggered.connect(lambda: self.parameters_requested.emit(self.label_text, self.otp_type))

        delete_action = QAction("Delete OTP code", self)
        delete_action.setObjectName("deleteAction")
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.label_text))

        menu.addAction(show_params_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        menu.exec(event.globalPos())

    def show_parameters(self):
        msg = QMessageBox(self)
        msg.setWindowTitle(f"Parameters")
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        msg.setText(self.parameter_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()


    def set_offline(self, reason: str = "Disconnected"):
        # Affiche un code neutre et un sous-titre explicite
        self.label_code.setText("●●●●●●")
        self.copy_button.setVisible(False)
        self.account_label.setText(reason)
        self.issuer_label.setText("")
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