from PyQt6.QtWidgets import QApplication
import sys
from ui.main_window import MainWindow
from pathlib import Path

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(Path('ui/style.qss').read_text())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
    