from PyQt6.QtWidgets import QApplication
import sys, re
from ui.main_window import MainWindow
from ui.ressources import resource_path

def load_qss_with_images(qss_rel_path=("ui","style.qss")) -> str:
    qss_path = resource_path(*qss_rel_path)
    css = qss_path.read_text(encoding="utf-8")

    # base absolute path to images (forward slashes pour Qt)
    img_base = resource_path("images").as_posix()

    # Remplace url("images/xxx.png") ou url(images/xxx.png) par un chemin absolu
    def repl(m):
        inner = m.group(1).strip().strip('"\'')
        if inner.startswith("images/") or inner.startswith("images\\"):
            new = f'{img_base}/{inner.split("/",1)[1] if "/" in inner else inner.split("\\\\",1)[1]}'
            return f'url("{new}")'
        return f'url("{inner}")'

    css = re.sub(r'url\(([^)]+)\)', repl, css)
    return css



if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    app.setStyleSheet(load_qss_with_images())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
    