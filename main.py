from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QSharedMemory, QSystemSemaphore
import sys, re, os
import tempfile
import atexit
from core.i18n_manager import setup_i18n
setup_i18n()
from ui.main_window import MainWindow
from ui.ressources import resource_path


class FileLockSingleton:
    def __init__(self, app_name="NeoOTP"):
        self.app_name = app_name
        self.lock_file = os.path.join(tempfile.gettempdir(), f"{app_name}.lock")
        self.pid = os.getpid()
        self.lock_handle = None  # Ajout pour garder le handle
                
        if self._check_existing_instance():
            print("❌ Instance déjà détectée")
            # Au lieu du warning, on sort silencieusement
            # L'instance existante va automatiquement revenir au premier plan
            sys.exit(0)
        
        # Créer le fichier de verrouillage
        self._create_lock()
        
        # Nettoyer automatiquement
        atexit.register(self.cleanup)
    
    def _check_existing_instance(self):
        """Vérifie si une instance existe déjà"""
        if not os.path.exists(self.lock_file):
            return False
        
        # D'abord tester si le fichier est verrouillé (instance active)
        try:
            # Essayer d'ouvrir en mode écriture exclusive
            with open(self.lock_file, 'r+') as f:
                content = f.read().strip()
                if not content:
                    print("Fichier lock vide - suppression")
                    return False
                
                pid = int(content)
                print(f"PID trouvé dans lock: {pid}")
                
                # Vérifier si le processus existe
                if self._process_exists(pid):
                    print("Processus existe encore")
                    self._try_bring_to_front(pid)
                    return True
                else:
                    print("Processus mort - fichier non verrouillé")
                    return False
                    
        except (IOError, OSError, PermissionError):
            # Le fichier est verrouillé = instance active
            print("Instance active détectée (fichier verrouillé)")
            self._try_bring_to_front(None)  # PID inconnu
            return True
            
        except Exception as e:
            print(f"Erreur test lock: {e}")
            return False
    
    def _process_exists(self, pid):
        """Vérifie si un processus existe"""
        try:
            if sys.platform == "win32":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(0x400, False, pid)
                if handle:
                    kernel32.CloseHandle(handle)
                    return True
                return False
            else:
                os.kill(pid, 0)
                return True
        except:
            return False
    
    def _try_bring_to_front(self, pid):
        """Essaie de ramener la fenêtre au premier plan (cross-platform)"""
        try:
            if sys.platform == "win32":
                # Windows
                import ctypes
                from ctypes import wintypes
                
                def enum_windows_callback(hwnd, windows):
                    if ctypes.windll.user32.IsWindowVisible(hwnd):
                        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                        if length > 0:
                            buffer = ctypes.create_unicode_buffer(length + 1)
                            ctypes.windll.user32.GetWindowTextW(hwnd, buffer, length + 1)
                            if "NeoOTP" in buffer.value or "Winkeo" in buffer.value:
                                ctypes.windll.user32.SetForegroundWindow(hwnd)
                                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                                return False
                    return True
                
                EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
                ctypes.windll.user32.EnumWindows(EnumWindowsProc(enum_windows_callback), 0)
                
            elif sys.platform == "darwin":
                # macOS
                import subprocess
                try:
                    # Chercher l'app par nom et la ramener au premier plan
                    subprocess.run([
                        "osascript", "-e", 
                        'tell application "System Events" to set frontmost of every process whose name contains "Python" to true'
                    ], check=False, capture_output=True)
                except:
                    pass
                    
            else:
                # Linux/Unix
                import subprocess
                try:
                    # Essayer avec wmctrl si disponible
                    result = subprocess.run(["which", "wmctrl"], capture_output=True)
                    if result.returncode == 0:
                        subprocess.run([
                            "wmctrl", "-a", "NeoOTP"
                        ], check=False, capture_output=True)
                    else:
                        # Fallback: essayer avec xdotool
                        result = subprocess.run(["which", "xdotool"], capture_output=True)
                        if result.returncode == 0:
                            subprocess.run([
                                "xdotool", "search", "--name", "NeoOTP", "windowactivate"
                            ], check=False, capture_output=True)
                except:
                    pass
                    
        except Exception as e:
            print(f"Erreur remise au premier plan: {e}")
            # Pas grave, on continue quand même
    
    def _create_lock(self):
        """Crée le fichier de verrouillage"""
        try:
            # Si un ancien fichier existe et n'est pas verrouillé, on peut le supprimer
            if os.path.exists(self.lock_file):
                try:
                    # Test rapide - si on peut l'ouvrir en écriture, il n'est pas verrouillé
                    with open(self.lock_file, 'r+') as f:
                        pass
                    # Arrivé ici = pas verrouillé, on peut le supprimer
                    os.remove(self.lock_file)
                    print("Ancien lock file non verrouillé supprimé")
                except (IOError, OSError, PermissionError):
                    # Verrouillé = il ne devrait pas y avoir d'autre instance
                    # mais au cas où, on continue quand même
                    print("Fichier existant verrouillé détecté")
            
            # Créer et garder ouvert le nouveau fichier
            self.lock_handle = open(self.lock_file, 'w')
            self.lock_handle.write(str(self.pid))
            self.lock_handle.flush()
            # Ne pas fermer le fichier - on le garde ouvert pour le verrouiller
            
        except Exception as e:
            print(f"Erreur création lock: {e}")
            sys.exit(1)
    
    def cleanup(self):
        """Nettoie le fichier de verrouillage"""
        # Éviter les appels multiples
        if not hasattr(self, 'cleanup_done'):
            self.cleanup_done = False
            
        if self.cleanup_done:
            return
            
        self.cleanup_done = True
        
        try:
            # Étape 1: Fermer le handle
            if self.lock_handle:
                try:
                    self.lock_handle.close()
                except Exception as e:
                    print(f"Erreur fermeture handle: {e}")
                finally:
                    self.lock_handle = None
            
            # Étape 2: Attendre un peu que Windows libère le fichier
            if os.path.exists(self.lock_file):
                import time
                
                # Vérifier d'abord que c'est notre fichier
                try:
                    with open(self.lock_file, 'r') as f:
                        content = f.read().strip()
                        if content != str(self.pid):
                            print(f"Lock file appartient à un autre processus ({content} vs {self.pid})")
                            return
                except Exception as e:
                    print(f"Impossible de lire le lock file: {e}")
                    return
                
                # Essayer de supprimer avec retry (Windows peut avoir besoin de temps)
                max_attempts = 5
                for attempt in range(max_attempts):
                    try:
                        os.remove(self.lock_file)
                        return
                    except (OSError, PermissionError) as e:
                        if attempt < max_attempts - 1:
                            print(f"Tentative {attempt + 1} échouée, retry dans 50ms...")
                            time.sleep(0.05)  # 50ms
                        else:
                            print(f"Impossible de supprimer après {max_attempts} tentatives: {e}")
                            print("Le fichier sera nettoyé au prochain démarrage")
                            
        except Exception as e:
            print(f"Erreur cleanup générale: {e}")

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

if hasattr(sys, 'frozen'):
    # Mode exécutable
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    
def main():    

    singleton = FileLockSingleton("NeoOTP")

    app = QApplication(sys.argv)    
    styles = load_qss_with_images()
    if styles:
        app.setStyleSheet(styles)
    window = MainWindow()    
    window.show()    

    # Plus besoin du try/finally car atexit s'en occupe
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())  # sys.exit() seulement ici