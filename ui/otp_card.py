# ui/otp_card.py
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
    parameters_requested = pyqtSignal(str, int)  # label, otp_type

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

        # === Layout principal ===
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 15, 5)

        # === Partie gauche ===
        left_widget = QWidget()
        left_widget.setFixedWidth(230)
        left_layout = QVBoxLayout(left_widget)

        # Code + copier
        self.label_code = QLabel()
        self.label_code.setObjectName("codeLabel")
        self.label_code.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        code_layout = QHBoxLayout()
        code_layout.addWidget(self.label_code)

        # Bouton copier
        copy_button_path = resource_path("images/copy.png")
        copy_button_clicked_path = resource_path("images/copy_clicked.png")
        from ui.main_window import IconButton
        self.copy_button = IconButton(copy_button_path, copy_button_clicked_path, QSize(16, 16))
        self.copy_button.setFixedSize(16, 16)
        self.copy_button.setFlat(True)
        self.copy_button.setToolTip("Copy code to clipboard")
        self.copy_button.setVisible(False)
        self.copy_button.clicked.connect(self.copy_code)

        self.feedback_label = QLabel("Code copied")
        self.feedback_label.setObjectName("CopiedLabel")
        self.feedback_label.setVisible(False)

        code_layout.addWidget(self.copy_button)
        code_layout.addWidget(self.feedback_label)
        code_layout.addStretch()

        # Labels de compte
        self.account_label = QLabel(f"{self.account}")
        self.account_label.setObjectName("accountName")
        self.account_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.issuer_label = QLabel(f"{self.issuer}")
        self.issuer_label.setObjectName("issuer")
        self.issuer_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        left_layout.addWidget(self.issuer_label)
        left_layout.addWidget(self.account_label)
        left_layout.addLayout(code_layout)

        main_layout.addWidget(left_widget)
        main_layout.addStretch()

        # === Partie droite compacte ===
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 30, 0, 0)
        right_layout.setSpacing(15)  # espace modéré entre les éléments

        # On ajoute un spacing en haut pour pousser légèrement vers le bas

        if otp_type == 1:  # HOTP
            refresh_icon_path = resource_path("images/refresh.png")
            refresh_icon_clicked_path = resource_path("images/refresh_clicked.png")
            self.btn = IconButton(refresh_icon_path, refresh_icon_clicked_path, QSize(35, 35))
            self.btn.setFlat(True)
            self.btn.clicked.connect(lambda: self.request_code.emit(self.label_text))
            right_layout.addWidget(self.btn, alignment=Qt.AlignmentFlag.AlignRight)
        else:  # TOTP
            self.progress = ProgressIndicator(period)
            right_layout.addWidget(self.progress, alignment=Qt.AlignmentFlag.AlignRight)

        # Boutons info + delete en bas à droite
        info_button_path = resource_path("images/info.png")
        info_button_clicked_path = resource_path("images/info_clicked.png")
        self.info_button = IconButton(info_button_path, info_button_clicked_path, QSize(16, 16))
        self.info_button.setFixedSize(16, 16)
        self.info_button.setFlat(True)
        self.info_button.setToolTip("Show OTP parameters")
        self.info_button.clicked.connect(lambda: self.parameters_requested.emit(self.label_text, self.otp_type))

        delete_button_path = resource_path("images/trash.png")
        delete_button_clicked_path = resource_path("images/trash_clicked.png")
        self.delete_button = IconButton(delete_button_path, delete_button_clicked_path, QSize(16, 16))
        self.delete_button.setFixedSize(16, 16)
        self.delete_button.setFlat(True)
        self.delete_button.setToolTip("Delete OTP account")
        self.delete_button.clicked.connect(lambda: self.delete_requested.emit(self.label_text))


        # Boutons info + delete juste en dessous
        bottom_buttons = QHBoxLayout()
        bottom_buttons.setSpacing(6)
        bottom_buttons.addStretch()
        bottom_buttons.addWidget(self.info_button)
        bottom_buttons.addWidget(self.delete_button)

        right_layout.addLayout(bottom_buttons)
    
        # Aligner toute la colonne verticalement au centre de la carte
        main_layout.addLayout(right_layout)
        main_layout.setAlignment(right_layout, Qt.AlignmentFlag.AlignVCenter)

        self.set_code(self.code)

    # --- méthodes utilitaires ---
    def format_code(self, code):
        code = str(code)
        if len(code) == 6:
            return code[:3] + " " + code[3:]
        elif len(code) == 7:
            return code[:4] + " " + code[4:]
        elif len(code) == 8:
            return code[:4] + " " + code[4:]
        else:
            return code

    def copy_code(self):
        code_with_spaces = self.label_code.text()
        code_without_spaces = code_with_spaces.replace(" ", "")
        QApplication.clipboard().setText(code_without_spaces)
        self.feedback_label.setVisible(True)
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
        if self.otp_type == 2:
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
        msg.setWindowTitle("Parameters")
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        msg.setText(self.parameter_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def set_offline(self, reason: str = "Disconnected"):
        self.label_code.setText("●●●●●●")
        self.copy_button.setVisible(False)
        self.info_button.setVisible(False)
        self.delete_button.setVisible(False)
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
        self.info_button.setVisible(True)
        self.delete_button.setVisible(True)
        if self.otp_type == 2:
            self.progress.setVisible(True)
        else:
            self.btn.setVisible(True)
        self.style().unpolish(self)
        self.style().polish(self)
