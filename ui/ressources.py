from pathlib import Path
import os
import sys

def resource_path(*parts: str) -> Path:
    # base = dossier temporaire PyInstaller quand gelé, sinon répertoire courant
    base = Path(getattr(sys, "_MEIPASS", os.getcwd()))
    return base.joinpath(*parts)