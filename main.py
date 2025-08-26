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
            # Au lieu du warning, on sort silencieusement
            # L'instance existante va automatiquement revenir au premier plan
            sys.exit(0)
        
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
                
                # Vérifier si le processus existe
                if self._process_exists(pid):
                    print("Processus existe encore")
                    # Essayer de ramener au premier plan via signal ou autre
                    self._try_bring_to_front(pid)
                    return True
                else:
                    print("Processus mort - suppression lock")
                    os.remove(self.lock_file)
                    return False
                    
        except Exception as e:
            print(f"Erreur lecture lock: {e}")
            try:
                os.remove(self.lock_file)
            except:
                pass
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
            with open(self.lock_file, 'w') as f:
                f.write(str(self.pid))
        except Exception as e:
            print(f"Erreur création lock: {e}")
            sys.exit(1)
    
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

    singleton = FileLockSingleton("NeoOTP")

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