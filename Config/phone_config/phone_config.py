# ./shared/utils/phone_config.py

# ./setting/config.py

import logging
import os
from typing import Dict, Tuple, List
from PySide6.QtCore import QSize, QSettings

# Application Configuration
APP_NAME: str = "NodeX"
APPLICATION_NAME: str = "NodeX"
COMPANY_NAME: str = "Rewnozom"
VERSION: str = "1.0.0"
DEBUG_MODE: bool = True

# Window Configuration
WINDOW_WIDTH: int = 400
WINDOW_HEIGHT: int = 400
DEFAULT_WINDOW_SIZE: QSize = QSize(WINDOW_WIDTH, WINDOW_HEIGHT)

# Layout Configuration
#ENABLE_PHONE_LAYOUT: bool = False
ENABLE_PHONE_LAYOUT: bool = True

# UI Constants
UI_LAYOUT_MARGINS: Tuple[int, int, int, int] = (10, 10, 10, 10)
UI_LAYOUT_SPACING: int = 10
UI_BUTTON_HEIGHT: int = 40
UI_ICON_SIZE: int = 24
UI_STATUS_TIMEOUT: int = 2000  # milliseconds

# Font Settings
UI_FONT_SIZES: Dict[str, str] = {
    'normal': '14px',
    'header': '16px'
}

# Theme Configuration
THEME_DARK: str = "dark"
THEME_LIGHT: str = "light"
THEME_OPTIONS: List[str] = [THEME_DARK, THEME_LIGHT]
DEFAULT_THEME: str = THEME_DARK
CURRENT_THEME: str = DEFAULT_THEME

# Theme Defaults
THEME_DEFAULTS: Dict[str, str] = {
    'font_family': 'Arial',
    'font_size': '14px',
    'default_color': '#FFFFFF',
    'default_spacing': '8px',
    'icon_size': '36px',
    'tab_padding': '10px'
}

# Paths and Directories
DESKTOP_LAYOUT_DIR: str = "./pages/desktop/Layout"
ANDROID_LAYOUT_DIR: str = "./pages/android/Layout"
CONSTANTS_DIR: str = os.path.join(PAGES_DIR, "Constants")
UTILS_DIR: str = os.path.join(PAGES_DIR, "Utils")
LOGS_DIR: str = os.path.join(PAGES_DIR, "Logs")
SYSTEM_PROMPTS_PATH: str = "./System_Prompts"
OUTPUT_DIRECTORY: str = "./output"
LOG_DIR: str = "logs"
LOG_FILE: str = "app.log"
INPUT_FILE: str = "./output_test.md"

# File Operations
FILE_ENCODING: str = 'utf-8'
FILE_EXTENSIONS: Dict[str, str] = {
    'python': '.py',
    'markdown': '.md'
}

# Logger Colors
LOG_COLORS: Dict[str, str] = {
    'DEBUG': '34',    # Blue
    'INFO': '32',     # Green
    'WARNING': '33',  # Yellow
    'ERROR': '31',    # Red
    'CRITICAL': '35'  # Magenta
}

# Choose logging level
CHOOSE_LOGGING_LEVEL: str = 'LVL1'  # Only `ERROR` and `CRITICAL` messages are logged.
# CHOOSE_LOGGING_LEVEL: str = 'LVL2'  # `WARNING`, `ERROR` and `CRITICAL` messages are logged.
# CHOOSE_LOGGING_LEVEL: str = 'LVL3'  # `INFO`, `WARNING`, `ERROR` and `CRITICAL` messages are logged.
# CHOOSE_LOGGING_LEVEL: str = 'LVL4'  # All messages including `DEBUG`, `INFO`, `WARNING`, `ERROR` and `CRITICAL` are logged.

# Logging level mapping
LOGGING_LEVEL_MAPPING: Dict[str, int] = {
    'LVL1': logging.ERROR,      # Only ERROR and CRITICAL
    'LVL2': logging.WARNING,    # WARNING, ERROR and CRITICAL
    'LVL3': logging.INFO,       # INFO, WARNING, ERROR and CRITICAL
    'LVL4': logging.DEBUG       # DEBUG, INFO, WARNING, ERROR and CRITICAL
}

# Set the actual logging level based on the chosen level
LOGGING_LEVEL: int = LOGGING_LEVEL_MAPPING.get(CHOOSE_LOGGING_LEVEL, logging.INFO)

# Available logging level options for configuration
CHOOSE_LOGGING_LEVEL_OPTIONS: List[str] = list(LOGGING_LEVEL_MAPPING.keys())

# Logging Configuration
LOGGING_LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR
}

LOGGING_LEVEL_STR: str = 'DEBUG' if DEBUG_MODE else 'INFO'
LOGGING_LEVEL: int = LOGGING_LEVEL_MAP[LOGGING_LEVEL_STR]
MAX_LOG_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT: int = 5
LOGGING_LEVEL_OPTIONS: List[str] = list(LOGGING_LEVEL_MAP.keys())

# Time Formats
LOG_TIMESTAMP_FORMAT: str = '%Y-%m-%d'
LOG_FILENAME_TEMPLATE: str = 'log_{timestamp}.log'

# Default Settings
AUTO_RUN_DEFAULT: bool = True  # Default for auto-run checkbox

# Error Messages
ERROR_MESSAGES: Dict[str, str] = {
    "page_not_found": "Page '{page_name}' not found.",
    "no_pages_discovered": "No pages were discovered. Check the 'Pages' directory and ensure page modules are correctly structured.",
    "failed_to_load_page": "Failed to load page '{page_name}': {error_msg}",
    "no_pages_available": "No pages available to load.",
}

# Sensitive Data Patterns for Logging
SENSITIVE_PATTERNS: List[str] = [
    'api_key',
    'jwt_secret',
    'ssh_password',
    'JWT_SECRET',
    'LLM_API_KEY',
]

# Settings Keys
LAST_PAGE_KEY: str = "last_page"
DEFAULT_LAST_PAGE: str = ""

# Feature Toggles
DEBUG_WORKFLOW: bool = True
ENABLE_BACKUP: bool = True
ENABLE_FORMATTING: bool = True
ENABLE_INTEGRATION: bool = True
ENABLE_REMOVAL: bool = True
ENABLE_VALIDATION: bool = True
ENABLE_VERSION_CONTROL: bool = False
STRICT_PARSING: bool = True
CREATE_MISSING_MODULES: bool = True
PRESERVE_FORMATTING: bool = True
USE_WORKSPACE_ROOT: bool = True

# Workspace Configuration
WORKSPACE_ROOT: str = "workspace"


class MobileConfig:
    """Configuration settings for mobile interface."""
    
    # Touch targets
    MINIMUM_TOUCH_TARGET = 48  # Minimum size in pixels for touchable elements
    
    # Animations
    ANIMATION_DURATION = 300  # Duration in milliseconds
    SHEET_ANIMATION_CURVE = "OutCubic"  # QEasingCurve type
    
    # Layout
    BOTTOM_SHEET_HEIGHT_RATIO = 0.7  # Height ratio of bottom sheets
    FAB_MARGIN = 16  # Margin for floating action button
    
    # Styling
    CORNER_RADIUS = {
        'small': 4,
        'medium': 8,
        'large': 12,
        'xl': 20
    }
    
    SPACING = {
        'xs': 4,
        'small': 8,
        'medium': 12,
        'large': 16,
        'xl': 24
    }
    
    # Gestures
    SWIPE_THRESHOLD = 50  # Minimum distance for swipe detection
    PINCH_SCALE_FACTOR = 1.5  # Scale factor for pinch zoom
    
    # Performance
    SCROLL_CHUNK_SIZE = 20  # Number of items to load at once in virtual lists
    
    @staticmethod
    def get_platform_adjustments():
        """Get platform-specific adjustments."""
        import sys
        if sys.platform == 'android':
            return {
                'touch_target': 56,  # Larger touch targets for Android
                'animation_duration': 250  # Slightly faster animations
            }
        elif sys.platform == 'ios':
            return {
                'touch_target': 44,  # iOS standard touch target
                'animation_duration': 300  # iOS standard animation duration
            }
        return {}


class ConfigManager:
    """Manages application configuration settings."""

    def __init__(self):
        self.settings = QSettings(COMPANY_NAME, APPLICATION_NAME)
        self.config = {}
        self.init_config()

    def init_config(self):
        """Initialize configuration settings."""
        try:
            self.config = {
                'app_name': APP_NAME,
                'theme': self.settings.value('theme', CURRENT_THEME),
                'window_size': self.settings.value('window_size', QSize(WINDOW_WIDTH, WINDOW_HEIGHT)),
                'last_page': self.settings.value(LAST_PAGE_KEY, ""),
                'last_page_key': LAST_PAGE_KEY,
                'icon_size': int(self.settings.value('icon_size', 24)),
                'enable_phone_layout': ENABLE_PHONE_LAYOUT,
                'desktop_layout_dir': DESKTOP_LAYOUT_DIR,
                'android_layout_dir': ANDROID_LAYOUT_DIR,
                'pages_dir': PAGES_DIR,
                'error_messages': ERROR_MESSAGES,
            }

            if self.config['theme'] not in THEME_OPTIONS:
                print(f"WARNING: Invalid theme '{self.config['theme']}'. Using default theme '{CURRENT_THEME}'.")
                self.config['theme'] = CURRENT_THEME

            if not isinstance(self.config['window_size'], QSize):
                print("WARNING: Invalid window size. Using default window size.")
                self.config['window_size'] = QSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        except Exception as e:
            print(f"ERROR: Error in init_config: {e}")
            self.config = {
                'app_name': APP_NAME,
                'theme': CURRENT_THEME,
                'window_size': QSize(WINDOW_WIDTH, WINDOW_HEIGHT),
                'last_page': "",
                'last_page_key': LAST_PAGE_KEY,
                'icon_size': 24,
                'enable_phone_layout': ENABLE_PHONE_LAYOUT,
                'desktop_layout_dir': DESKTOP_LAYOUT_DIR,
                'android_layout_dir': ANDROID_LAYOUT_DIR,
                'pages_dir': PAGES_DIR,
                'error_messages': ERROR_MESSAGES,
            }

    def get(self, key, default=None):
        """Get a configuration value with an optional default."""
        return self.config.get(key, default)

    def set(self, key, value):
        """Set a configuration value."""
        self.config[key] = value
        # For persistent settings, also save to QSettings
        if key in ['theme', 'window_size', 'icon_size']:
            self.settings.setValue(key, value)

    def save_config(self):
        """Save configuration settings."""
        try:
            self.settings.setValue('theme', self.config['theme'])
            self.settings.setValue('window_size', self.config['window_size'])
            self.settings.setValue('icon_size', self.config['icon_size'])
        except Exception as e:
            print(f"ERROR: Error saving config: {e}")

    def save_chat_settings(self, settings):
        """Save chat-specific settings."""
        try:
            for key, value in settings.items():
                self.set(f'chat_{key}', value)
        except Exception as e:
            print(f"ERROR: Error saving chat settings: {e}")

    def load_chat_settings(self):
        """Load chat-specific settings."""
        try:
            return {key.replace('chat_', ''): value 
                   for key, value in self.config.items() 
                   if key.startswith('chat_')}
        except Exception as e:
            print(f"ERROR: Error loading chat settings: {e}")
            return {}

    def save_left_menu_state(self, state):
        """Save left menu state."""
        try:
            self.set('left_menu_state', state)
        except Exception as e:
            print(f"ERROR: Error saving left menu state: {e}")

    def load_left_menu_state(self):
        """Load left menu state."""
        try:
            return self.get('left_menu_state', {})
        except Exception as e:
            print(f"ERROR: Error loading left menu state: {e}")
            return {}