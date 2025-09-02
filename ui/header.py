# ui/header.py - Version corrigée pour équilibrer les tailles

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QSize
from ui.ressources import resource_path
from PyQt6.QtSvgWidgets import QSvgWidget

class ScalableSvgWidget(QSvgWidget):
    """SVG Widget qui maintient les proportions avec taille spécifique"""
    def __init__(self, svg_path, target_height, parent=None):
        super().__init__(str(svg_path), parent)
        self.target_height = target_height
        self._setup_scaling()
    
    def _setup_scaling(self):
        # Obtenir la taille naturelle du SVG
        renderer = self.renderer()
        if renderer.isValid():
            natural_size = renderer.defaultSize()
            aspect_ratio = natural_size.width() / natural_size.height()
            
            # Calculer la largeur basée sur la hauteur cible
            scaled_width = int(self.target_height * aspect_ratio)
            
            # Appliquer la taille
            self.setFixedSize(scaled_width, self.target_height)

class Header(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("header")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(65)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Hauteurs spécifiques par logo pour équilibrer visuellement
        # Ajustez ces valeurs selon vos besoins
        neowave_height = 40
        otp_height = 20      # Plus petit car probablement trop gros
        manager_height = 10
        
        # Logos avec tailles ajustées individuellement
        logo_neowave_path = resource_path("images", "neowave.svg")
        logo_neowave = ScalableSvgWidget(logo_neowave_path, neowave_height)
        
        logo_otp_path = resource_path("images", "otp_regular.svg")
        logo_otp = ScalableSvgWidget(logo_otp_path, otp_height)  # Plus petit
        
        logo_manager_path = resource_path("images", "manager_man_noir.svg")
        logo_manager = ScalableSvgWidget(logo_manager_path, manager_height)

        # Container pour les logos avec espacement contrôlé
        logos_widget = QWidget()
        logos_layout = QHBoxLayout(logos_widget)
        logos_layout.setContentsMargins(0, 0, 0, 0)
        logos_layout.setSpacing(5)  # Petit espacement entre logos
        
        # Ajouter avec alignement parfait
        logos_layout.addWidget(logo_neowave, alignment=Qt.AlignmentFlag.AlignCenter)
        logos_layout.addWidget(logo_otp, alignment=Qt.AlignmentFlag.AlignCenter)
        logos_layout.addWidget(logo_manager, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Centrer le groupe de logos
        layout.addStretch()
        layout.addWidget(logos_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()