# ui/header.py - Version avec une seule image

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from ui.ressources import resource_path
from PyQt6.QtSvgWidgets import QSvgWidget

class Header(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("header")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(65)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo unique centré avec proportions correctes
        logo_path = resource_path("images", "logo_full_noir.svg")
        logo = QSvgWidget(str(logo_path))
        
        # Définir une hauteur et laisser le SVG calculer la largeur proportionnelle
        target_height = 22  # Hauteur désirée
        logo.setFixedHeight(target_height)
        
        # Obtenir la taille naturelle pour calculer la largeur proportionnelle
        renderer = logo.renderer()
        if renderer.isValid():
            natural_size = renderer.defaultSize()
            if natural_size.height() > 0:
                aspect_ratio = natural_size.width() / natural_size.height()
                scaled_width = int(target_height * aspect_ratio)
                logo.setFixedWidth(scaled_width)
        
        # Centrer le logo
        layout.addStretch()
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()