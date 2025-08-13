# ui/header.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class Header(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("header")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # ← important
        self.setFixedHeight(65)
        layout = QHBoxLayout(self)
    
        #layout.setContentsMargins(0, 15, 0, 15)
        layout.setSpacing(0)

        pixmap = QPixmap("images/logo.png")
        label_logo = QLabel()
        label_logo.setPixmap(pixmap.scaled(
            35, 35,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))
        label_logo.setScaledContents(False)

        label_titre = QLabel("NEOWAVE OTP MANAGER")
        label_titre.setObjectName("titreApp")

        layout.addStretch()
        layout.addWidget(label_logo)
        layout.addWidget(label_titre)
        layout.addStretch()
