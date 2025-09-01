# core/logger.py - Nouveau fichier pour la configuration du logging

import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(name="NeoOTP", log_level=logging.DEBUG):
    """Configure le système de logging"""
    
    # Créer le dossier de logs
    if getattr(sys, 'frozen', False):
        # Mode PyInstaller
        log_dir = Path(os.path.dirname(sys.executable)) / "logs"
    else:
        # Mode développement
        log_dir = Path(__file__).parent.parent / "logs"
    
    log_dir.mkdir(exist_ok=True)
    
    # Nom du fichier avec timestamp
    log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Créer le logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Éviter les handlers multiples
    if logger.handlers:
        return logger
    
    # Format des messages
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-12s | %(funcName)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler pour fichier avec rotation (max 10MB, 5 fichiers)
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Handler pour console (optionnel)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Moins verbeux en console
    console_handler.setFormatter(logging.Formatter(
        '%(levelname)-8s | %(name)-12s | %(message)s'
    ))
    
    # Ajouter les handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log de démarrage
    logger.info("="*60)
    logger.info(f"Logging initialized - Log file: {log_file}")
    logger.info("="*60)
    
    return logger

# Instance globale
app_logger = setup_logger()