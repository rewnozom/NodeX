# ..\dynamic_main\icon_manager.py

# dynamic_main/icon_manager.py

from PySide6.QtGui import QIcon
from Config import ICONS
from log.logger import logger

class IconManager:

    def __init__(self, main_window):
        self.main_window = main_window

    def setup_icons(self):
        for key, path in ICONS.items():
            try:
                icon = QIcon(path)
                if icon.isNull():
                    logger.warning(f"Icon '{key}' not found or is invalid at path: {path}")
                else:
                    setattr(self.main_window, f"{key}_icon", icon)
            except Exception as e:
                logger.error(f"Error loading icon '{key}': {e}")
