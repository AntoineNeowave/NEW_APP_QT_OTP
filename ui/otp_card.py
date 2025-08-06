# ui/otp_card.py
from PyQt6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar,
    QMenu, QMessageBox, QApplication, QToolTip
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, pyqtSignal, QSize
import time

class OTPCard(QFrame):
    request_code = pyqtSignal(str)  # signal avec le label
    delete_requested = pyqtSignal(str)

    def __init__(self, label: str, code: str, parameters: str, otp_type: int, period: int, parent=None):
        super().__init__(parent)
        self.label_text = label
        self.otp_type = otp_type
        self.period = period
        self.remaining_seconds = 0
        self.parameter_text = parameters

        self.setObjectName("otpCard")

        main_layout = QHBoxLayout(self)

        # Labels
        text_layout = QVBoxLayout()
        self.label_code = QLabel(f"{code}")
        self.label_code.setObjectName("codeLabel")
        self.label_code.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        code_layout = QHBoxLayout()
        code_layout.addWidget(self.label_code)
        copy_button = QPushButton(QIcon("images/copier.png"), "")
        copy_button.setFixedSize(24, 24)
        copy_button.setFlat(True)
        copy_button.setToolTip("Copier le code")
        copy_button.clicked.connect(lambda: 
            QApplication.clipboard().setText(self.label_code.text()),
        )
        code_layout.addWidget(copy_button)

        self.account = QLabel(f"{label}")
        self.account.setObjectName("accountName")
        self.issuer = QLabel(f"{label}")
        self.issuer.setObjectName("issuer")
        text_layout.addWidget(self.account)
        text_layout.addWidget(self.issuer)
        text_layout.addLayout(code_layout)

        main_layout.addLayout(text_layout)
        main_layout.addStretch()

        if otp_type == 1:
            btn = QPushButton()
            btn.setIcon(QIcon("images/refresh.png"))
            btn.setIconSize(QSize(27, 27))
            btn.setFixedSize(27, 27)
            btn.setFlat(True)
            btn.clicked.connect(lambda: self.request_code.emit(self.label_text))
            main_layout.addWidget(btn)
        else:
            self.progress = QProgressBar()
            self.progress.setObjectName("progressBar")
            self.progress.setMinimum(0)
            self.progress.setMaximum(self.period)
            self.progress.setTextVisible(False)
            self.progress.setFixedWidth(120)
            self.progress.setFixedHeight(15)
            main_layout.addWidget(self.progress)
        
        main_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

    def set_code(self, code: str):
        self.label_code.setText(f"{code}")

    def update_progress_value(self, now: float):
        if hasattr(self, 'progress'):
            elapsed = now % self.period
            self.remaining_seconds = int(self.period - elapsed)
            self.progress.setValue(round(elapsed))


    def contextMenuEvent(self, event):
        menu = QMenu(self)

        show_params_action = QAction("Afficher les paramètres", self)
        show_params_action.triggered.connect(self.show_parameters)

        delete_action = QAction("Supprimer", self)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.label_text))

        menu.addAction(show_params_action)
        menu.addAction(delete_action)
        menu.exec(event.globalPos())

    def show_parameters(self):
        msg = QMessageBox(self)
        msg.setWindowTitle(f"Paramètres - {self.label_text}")
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        msg.setText(self.parameter_text)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()