# ui/otp_card.py
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, pyqtSignal
import time

class OTPCard(QFrame):
    request_code = pyqtSignal(str)  # signal avec le label

    def __init__(self, label: str, code: str, subtitle: str, otp_type: int, parent=None):
        super().__init__(parent)
        self.label_text = label
        self.otp_type = otp_type
        self.period = 30
        self.remaining_seconds = 0

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
        circle = QLabel("T" if otp_type == 2 else "H")
        circle.setFixedSize(32, 32)
        circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        circle.setStyleSheet(f"border-radius: 16px; background-color: {'#007bff' if otp_type == 2 else '#FFA500'}; color: white;")

        # Labels
        text_layout = QVBoxLayout()
        self.label_code = QLabel(f"<b>{code}</b>")
        self.label_main = QLabel(label)
        self.label_sub = QLabel(subtitle)
        text_layout.addWidget(self.label_code)
        text_layout.addWidget(self.label_main)
        text_layout.addWidget(self.label_sub)

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
