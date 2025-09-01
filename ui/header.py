# ui/header.py - Version avancée avec contrôle précis

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QSize
from ui.ressources import resource_path
from PyQt6.QtSvgWidgets import QSvgWidget

class ScalableSvgWidget(QSvgWidget):
    """SVG Widget qui maintient les proportions"""
    def __init__(self, svg_path, max_height=45, parent=None):
        super().__init__(str(svg_path), parent)
        self.max_height = max_height
        self._setup_scaling()
    
    def _setup_scaling(self):
        # Obtenir la taille naturelle du SVG
        renderer = self.renderer()
        if renderer.isValid():
            natural_size = renderer.defaultSize()
            aspect_ratio = natural_size.width() / natural_size.height()
            
            # Calculer la largeur basée sur la hauteur max
            scaled_width = int(self.max_height * aspect_ratio)
            
            # Appliquer la taille
            self.setFixedSize(scaled_width, self.max_height)

class Header(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("header")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(65)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # SVG avec scaling automatique et proportions préservées
        max_logo_height = 40
        
        # Logos avec scaling intelligent
        logo_neowave_path = resource_path("images", "neowave.svg")
        logo_neowave = ScalableSvgWidget(logo_neowave_path, max_logo_height)
        
        logo_otp_path = resource_path("images", "otp.svg")
        logo_otp = ScalableSvgWidget(logo_otp_path, max_logo_height)
        
        logo_manager_path = resource_path("images", "manager.svg")
        logo_manager = ScalableSvgWidget(logo_manager_path, max_logo_height)

        # Container pour les logos avec espacement contrôlé
        logos_widget = QWidget()
        logos_layout = QHBoxLayout(logos_widget)
        logos_layout.setContentsMargins(0, 0, 0, 0)
        logos_layout.setSpacing(0)  # Espacement entre logos
        
        # Ajouter avec alignement parfait
        logos_layout.addWidget(logo_neowave, alignment=Qt.AlignmentFlag.AlignCenter)
        logos_layout.addWidget(logo_otp, alignment=Qt.AlignmentFlag.AlignCenter)
        logos_layout.addWidget(logo_manager, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Centrer le groupe de logos
        layout.addStretch()
        layout.addWidget(logos_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()