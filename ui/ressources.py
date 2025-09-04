# ui/ressources_fixed.py
from pathlib import Path
import os
import sys

def resource_path(*parts: str) -> Path:
    """
    Gestion des ressources compatible Nuitka/PyInstaller
    """
    # 1. PyInstaller (sys._MEIPASS)
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
        return base.joinpath(*parts)
    
    # 2. Nuitka onefile mode
    if hasattr(sys, "frozen") and sys.frozen:
        # Nuitka stocke les données dans un dossier temporaire
        # Chercher dans plusieurs emplacements possibles
        possible_paths = [
            # Dans le dossier temporaire Nuitka
            Path(os.environ.get('TEMP', '')) / f"onefile_{os.getpid()}" / "nuitka_onefile_parent",
            # À côté de l'exe
            Path(sys.executable).parent,
            # Dans le répertoire courant
            Path.cwd(),
        ]
        
        for base_path in possible_paths:
            if base_path.exists():
                resource_file = base_path.joinpath(*parts)
                if resource_file.exists():
                    return resource_file
        
        # Si rien n'est trouvé, retourner le premier chemin pour debug
        return possible_paths[1].joinpath(*parts)
    
    # 3. Mode développement
    if __file__:
        project_root = Path(__file__).parent.parent
    else:
        project_root = Path.cwd()
        
    return project_root.joinpath(*parts)