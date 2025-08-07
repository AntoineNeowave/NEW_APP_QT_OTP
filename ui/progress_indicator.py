# ui/progress_indicator.py
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush

class ProgressIndicator(QWidget):
    def __init__(self, period: int, parent=None):
        super().__init__(parent)
        self.period = period
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(12)
        self.setMaximumWidth(300)
        self.setMinimumWidth(100)

        self._progress = 0.0  # entre 0.0 et 1.0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(16)  # ~60 FPS

    def update_progress(self):
        import time
        now = time.time()
        phase = now % self.period
        self._progress = phase / self.period
        self.update()  # déclenche le paintEvent()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dimensions
        w = self.width()
        h = self.height()
        r = h / 2

        # Bord arrondi
        bg_brush = QBrush(QColor("#cceeff"))
        fill_brush = QBrush(QColor("#36bcff"))

        # Arrière-plan
        painter.setBrush(bg_brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, w, h, r, r)

        # Remplissage progressif
        fill_width = w * self._progress
        painter.setBrush(fill_brush)
        painter.drawRoundedRect(0, 0, int(fill_width), h, r, r)


        painter.end()
