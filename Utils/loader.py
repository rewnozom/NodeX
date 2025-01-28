# ./frontend/pages/Utils/loader.py

import os
import importlib
from typing import Optional, Any, List
from PySide6.QtWidgets import QWidget
from log.logger import logger

def load_module(module_path: str) -> Optional[Any]:
    """Dynamiskt ladda en modul baserat på modulens sökväg."""
    try:
        module = importlib.import_module(module_path)
        logger.debug(f"Modul '{module_path}' laddad framgångsrikt.")
        return module
    except ImportError as e:
        logger.error(f"ImportError när modul '{module_path}' laddades: {e}")
    except SyntaxError as e:
        logger.error(f"SyntaxError i modul '{module_path}': {e}")
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

def has_page_module(directory: str) -> bool:
    """Check if the directory contains a 'Page.py' file."""
    page_py = os.path.join(directory, 'Page.py')
    exists = os.path.isfile(page_py)
    logger.debug(f"Checking for 'Page.py' in '{directory}': {'Found' if exists else 'Not Found'}")
    return exists
