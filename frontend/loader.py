# ./frontend/pages/Utils/loader.py

import os
import importlib
from typing import Optional, Any
from PySide6.QtWidgets import QWidget
from log.logger import logger
from typing import Dict, Tuple, List

def load_module(module_path: str) -> Optional[Any]:
    """Dynamiskt ladda en modul baserat på modulens sökväg."""
    try:
        module = importlib.import_module(module_path)
        logger.debug(f"Modul '{module_path}' laddad framgångsrikt.")
        return module
    except ImportError as e:
        logger.error(f"ImportError när modul '{module_path}' laddades: {e}")
    except Exception as e:
        logger.error(f"Fel vid laddning av modul '{module_path}': {e}")
    return None

def get_subdirectories(directory: str) -> List[str]:
    """Hämta en lista över alla undermappar i en given katalog."""
    try:
        subdirs = [name for name in os.listdir(directory) 
                   if os.path.isdir(os.path.join(directory, name))]
        logger.debug(f"Found subdirectories in '{directory}': {subdirs}")
        return subdirs
    except Exception as e:
        logger.error(f"Fel vid hämtning av undermappar i '{directory}': {e}")
        return []
