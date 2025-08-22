# ui/progress_indicator.py
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QBrush

class ProgressIndicator(QWidget):
    def __init__(self, period=30, parent=None):
        super().__init__(parent)
        self.period = period
        self.remaining_seconds = 0
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(12)
        self.setMaximumWidth(300)
        self.setMinimumWidth(100)
        
    def update_progress_value(self, current_time):
        """Met à jour la valeur de progression basée sur le temps actuel"""
        cycle_position = current_time % self.period
        self.remaining_seconds = self.period - cycle_position
        self.update()  # Déclenche un repaint
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dimensions
        w = self.width()
        h = self.height()
        r = h / 2

        # Bord arrondi
        bg_brush = QBrush(QColor("#c3e9fc"))
        fill_brush = QBrush(QColor("#52c5e4"))

        # Arrière-plan
        painter.setBrush(bg_brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, w, h, r, r)

        # Remplissage progressif
        fill_ratio = self.remaining_seconds / self.period
        fill_width = int(w * fill_ratio)
        painter.setBrush(fill_brush)
        painter.drawRoundedRect(0, 0, int(fill_width), h, r, r)


        painter.end()
