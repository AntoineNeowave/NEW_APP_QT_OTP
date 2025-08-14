from PyQt6.QtWidgets import QApplication
import sys
from ui.main_window import MainWindow
from pathlib import Path

from pathlib import Path
import sys
import os

def resource_path(*parts: str) -> Path:
    # base = dossier temporaire PyInstaller quand gelé, sinon répertoire courant
    base = Path(getattr(sys, "_MEIPASS", os.getcwd()))
    return base.joinpath(*parts)

# Chargement de la feuille de style
qss_path = resource_path("ui", "style.qss")
style = qss_path.read_text(encoding="utf-8")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(style)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
    