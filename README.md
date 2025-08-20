# NEOWAVE OTP MANAGER
**Application pour gérer et retrouver facilement vos codes 2FA OTP en toute sécurité avec votre token Neowave**

## Utilisation

- Branchez votre token Neowave
- Enrollez votre seed
- Récupérez votre code

## Installation

### Linux:
- Créer un environnement: `python -m venv venv`
- L'activer: `source venv/bin/activate`
- Installer les dépendances: `pip install -r requirements.txt`

### Windows:
...
### MacOS:
...

Lancement: python ./main.py

## Générer un executable:

### Linux:

#### Installation des headers et libs de développement (une seule fois)
#### Ubuntu/Debian :
sudo apt install python3-dev libusb-1.0-0-dev libudev-dev libpcsclite-dev

#### CentOS/Fedora :
sudo dnf install python3-devel libusb1-devel libudev-devel pcsc-lite-devel

### Windows:

Lancer `./build.bat`
PyInstaller va inclure automatiquement la plupart des DLLs nécessaires
L'executable se trouve dans 'dist'

### MacOS:

## Lancement de l'executable:

### Linux:
Libraries système requises

#### Ubuntu/Debian (utilisateur final) :
sudo apt install libusb-1.0-0 pcscd libpcsclite1 libhidapi-hidraw0

#### CentOS/Fedora (utilisateur final) :
sudo dnf install libusb1 pcsc-lite hidapi

### Windows:
Aucune installation requise !

PyInstaller inclut tout dans le onefile
L'utilisateur a juste besoin de :
- Windows 10/11
- Droits admin