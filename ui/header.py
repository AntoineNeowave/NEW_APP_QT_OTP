# ui/header.py
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from ui.ressources import resource_path
from PyQt6.QtSvgWidgets import QSvgWidget

class Header(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("header")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # ← important
        self.setFixedHeight(65)
        layout = QHBoxLayout(self)
    
        #layout.setContentsMargins(0, 15, 0, 15)
        layout.setSpacing(0)
        logo_path = resource_path("images", "logo_svg_white.svg")
        logo = QSvgWidget(str(logo_path))   # ← cast en str
        logo.setFixedSize(170, 50)  # dimensions fixes mais rendu vectoriel

        label_titre = QLabel("OTP MANAGER")
        label_titre.setObjectName("titreApp")

        layout.addStretch()
        layout.addWidget(logo)
        layout.addWidget(label_titre)
        layout.addStretch()
