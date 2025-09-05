import gettext
import os
from pathlib import Path
import locale

def setup_i18n():
    """Configure l'internationalisation au démarrage de l'app"""
    
    # Répertoire des traductions (à côté de main.py)
    locales_dir = Path(__file__).parent.parent / "locales"
    
    # Détecter la langue du système
    try:
        language, _ = locale.getdefaultlocale()  # ex: ('fr_FR', 'UTF-8')
        if not language:
            language = "en"
        language = language.split('_')[0]  # 'fr_FR' -> 'fr'
    except Exception:
        language = "en"
        
    # Nom de domaine (doit correspondre au nom de vos fichiers .po/.mo)
    domain = 'messages'
    
    try:
        if language != 'en' and locales_dir.exists():
            # Charger la traduction
            translation = gettext.translation(
                domain,
                localedir=str(locales_dir),
                languages=[language],
                fallback=True
            )
        else:
            # Pas de traduction (anglais ou fichier non trouvé)
            translation = gettext.NullTranslations()
            
        # Installer globalement
        translation.install()
        
        # Créer la fonction _ globale
        import builtins
        builtins._ = translation.gettext
        
    except Exception as e:
        print(f"Erreur i18n: {e}")
        # En cas d'erreur, créer une fonction _ qui ne fait rien
        import builtins
        builtins._ = lambda x: x