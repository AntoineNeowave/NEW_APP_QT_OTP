from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QSharedMemory, QSystemSemaphore
import sys, re, os
from ui.main_window import MainWindow
from ui.ressources import resource_path

import os
import sys
import tempfile
import time
import atexit
from PyQt6.QtWidgets import QApplication, QMessageBox

class FileLockSingleton:
    def __init__(self, app_name="NeoOTP"):
        self.app_name = app_name
        self.lock_file = os.path.join(tempfile.gettempdir(), f"{app_name}.lock")
        self.pid = os.getpid()
        
        print(f"Début singleton fichier: {self.lock_file}")
        
        if self._check_existing_instance():
            print("❌ Instance déjà détectée")
            self._show_already_running_message()
            sys.exit(1)
        
        # Créer le fichier de verrouillage
        self._create_lock()
        print("✅ Première instance - lock créé")
        
        # Nettoyer automatiquement
        atexit.register(self.cleanup)
    
    def _check_existing_instance(self):
        """Vérifie si une instance existe déjà"""
        if not os.path.exists(self.lock_file):
            return False
        
        try:
            with open(self.lock_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    return False
                
                pid = int(content)
                print(f"PID trouvé dans lock: {pid}")
                
                # Vérifier si le processus existe (cross-platform)
                if self._process_exists(pid):
                    print("Processus existe encore")
                    return True
                else:
                    print("Processus mort - suppression lock")
                    os.remove(self.lock_file)
                    return False
                    
        except Exception as e:
            print(f"Erreur lecture lock: {e}")
            # Fichier corrompu, le supprimer
            try:
                os.remove(self.lock_file)
            except:
                pass
            return False
    
    def _process_exists(self, pid):
        """Vérifie si un processus existe (cross-platform)"""
        try:
            if sys.platform == "win32":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(0x400, False, pid)  # PROCESS_QUERY_INFORMATION
                if handle:
                    kernel32.CloseHandle(handle)
                    return True
                return False
            else:
                # Unix/Linux/Mac
                os.kill(pid, 0)
                return True
        except:
            return False
    
    def _create_lock(self):
        """Crée le fichier de verrouillage"""
        try:
            with open(self.lock_file, 'w') as f:
                f.write(str(self.pid))
        except Exception as e:
            print(f"Erreur création lock: {e}")
            sys.exit(1)
    
    def _show_already_running_message(self):
        """Affiche le message d'instance déjà en cours"""
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
                temp_app = True
            else:
                temp_app = False
            
            QMessageBox.warning(
                None,
                "NeoOTP already running",
                "NeoOTP application is already running.\n\n"
                "Check the notification area or close the existing instance."
            )
            
            if temp_app:
                app.processEvents()
                time.sleep(1)
                
        except Exception as e:
            print(f"Erreur affichage message: {e}")
    
    def cleanup(self):
        """Nettoie le fichier de verrouillage"""
        try:
            if os.path.exists(self.lock_file):
                with open(self.lock_file, 'r') as f:
                    if f.read().strip() == str(self.pid):
                        os.remove(self.lock_file)
                        print("Lock file supprimé")
        except:
            pass

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

def main():    

    singleton = FileLockSingleton("NeoOTP_V0.0.3")

    app = QApplication(sys.argv)    
    app.setStyleSheet(load_qss_with_images())    
    window = MainWindow()    
    window.show()    

    try:
        result = app.exec()
    finally:
        singleton.cleanup()
    
    return result

if __name__ == "__main__":
    sys.exit(main())  # sys.exit() seulement ici