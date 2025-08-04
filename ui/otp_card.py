# ui/otp_card.py
from PyQt6.QtWidgets import (
    QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar,
    QMenu, QMessageBox, QApplication, QToolTip
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
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

        self.setFrameShape(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 10px;
                padding: 10px;
                margin: 4px;
            }
        """)

        main_layout = QHBoxLayout(self)

        # Circle
        circle = QLabel("TOTP" if otp_type == 2 else "HOTP")
        circle.setFixedSize(60, 60)
        circle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Labels
        text_layout = QVBoxLayout()
        self.label_code = QLabel(f"<b>{code}</b>")
        self.label_code.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        code_layout = QHBoxLayout()
        code_layout.addWidget(self.label_code)
        copy_button = QPushButton("📃")
        copy_button.setFixedSize(24, 24)
        copy_button.setFlat(True)
        copy_button.setStyleSheet("font-size: 14px; padding: 0px;")
        copy_button.setToolTip("Copier le code")
        copy_button.clicked.connect(lambda: (
            QApplication.clipboard().setText(self.label_code.text()),
            QToolTip.showText(copy_button.mapToGlobal(QPoint(0, 0)), "Code copié !")
        ))
        code_layout.addWidget(copy_button)

        self.label_main = QLabel(label)
        text_layout.addLayout(code_layout)
        text_layout.addWidget(self.label_main)

        main_layout.addWidget(circle)
        main_layout.addLayout(text_layout)
        main_layout.addStretch()

        if otp_type == 1:
            btn = QPushButton()
            btn.setIcon(QIcon.fromTheme("view-refresh"))
            btn.setFixedSize(24, 24)
            btn.setFlat(True)
            btn.clicked.connect(lambda: self.request_code.emit(self.label_text))
            main_layout.addWidget(btn)
        else:
            self.progress = QProgressBar()
            self.progress.setMinimum(0)
            self.progress.setMaximum(self.period)
            self.progress.setFixedWidth(80)
            main_layout.addWidget(self.progress)

    def set_code(self, code: str):
        self.label_code.setText(f"<b>{code}</b>")

    def update_progress(self, period: int):
        self.period = period
        now = int(time.time())
        self.remaining_seconds = now % self.period
        if hasattr(self, 'progress'):
            self.progress.setValue(self.remaining_seconds)

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