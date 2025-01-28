#!/usr/bin/env python3
# ./Config/AppConfig/config.py

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
ENABLE_PHONE_LAYOUT: bool = False

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
THEME_LIGHT: str = ""
THEME_OPTIONS: List[str] = [THEME_DARK]
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
DESKTOP_LAYOUT_DIR: str = "./frontend/Pages/desktop/Layout"
ANDROID_LAYOUT_DIR: str = "./frontend/Pages/android/Layout"
CONSTANTS_DIR: str = "./frontend/Pages/Constants"
UTILS_DIR: str = "./Utils"
LOGS_DIR: str = "./logs"
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

# Logging Configuration
DEBUG_LOGGING: bool = True

# Logging Levels
LOGGING_LEVELS = {
    'LVL1': {'level': logging.ERROR, 'description': 'Only ERROR and CRITICAL'},
    'LVL2': {'level': logging.WARNING, 'description': 'WARNING, ERROR and CRITICAL'},
    'LVL3': {'level': logging.INFO, 'description': 'INFO, WARNING, ERROR and CRITICAL'},
    'LVL4': {'level': logging.DEBUG, 'description': 'All messages including DEBUG'}
}

CHOOSE_LOGGING_LEVEL: str = 'LVL4'  # Default to most verbose logging
LOGGING_LEVEL: int = LOGGING_LEVELS[CHOOSE_LOGGING_LEVEL]['level']

# Logger Colors
LOG_COLORS: Dict[str, str] = {
    'DEBUG': '34',    # Blue
    'INFO': '32',     # Green
    'WARNING': '33',  # Yellow
    'ERROR': '31',    # Red
    'CRITICAL': '35'  # Magenta
}

# Logger Settings
MAX_LOG_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT: int = 5
LOG_TIMESTAMP_FORMAT: str = '%Y-%m-%d'
LOG_FILENAME_TEMPLATE: str = 'log_{timestamp}.log'

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
                'error_messages': ERROR_MESSAGES,
                'logging_level': LOGGING_LEVEL,
                'debug_logging': DEBUG_LOGGING
            }

            self._validate_config()
        except Exception as e:
            print(f"ERROR: Error in init_config: {e}")
            self._set_default_config()

    def _validate_config(self):
        """Validate configuration values and set defaults if invalid."""
        if self.config['theme'] not in THEME_OPTIONS:
            print(f"WARNING: Invalid theme '{self.config['theme']}'. Using default theme '{CURRENT_THEME}'.")
            self.config['theme'] = CURRENT_THEME

        if not isinstance(self.config['window_size'], QSize):
            print("WARNING: Invalid window size. Using default window size.")
            self.config['window_size'] = QSize(WINDOW_WIDTH, WINDOW_HEIGHT)

    def _set_default_config(self):
        """Set default configuration values."""
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
            'error_messages': ERROR_MESSAGES,
            'logging_level': LOGGING_LEVEL,
            'debug_logging': DEBUG_LOGGING
        }

    def get(self, key, default=None):
        """Get a configuration value with an optional default."""
        return self.config.get(key, default)

    def set(self, key, value):
        """Set a configuration value."""
        self.config[key] = value
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

    def get_logging_level(self) -> int:
        """Get current logging level."""
        return self.config.get('logging_level', LOGGING_LEVEL)

# Export all variables
__all__ = [
    'APP_NAME', 'APPLICATION_NAME', 'COMPANY_NAME', 'VERSION', 'DEBUG_MODE',
    'WINDOW_WIDTH', 'WINDOW_HEIGHT', 'DEFAULT_WINDOW_SIZE',
    'ENABLE_PHONE_LAYOUT',
    'UI_LAYOUT_MARGINS', 'UI_LAYOUT_SPACING', 'UI_BUTTON_HEIGHT', 
    'UI_ICON_SIZE', 'UI_STATUS_TIMEOUT',
    'UI_FONT_SIZES',
    'THEME_DARK', 'THEME_LIGHT', 'THEME_OPTIONS', 'DEFAULT_THEME', 
    'CURRENT_THEME', 'THEME_DEFAULTS',
    'DESKTOP_LAYOUT_DIR', 'ANDROID_LAYOUT_DIR', 'CONSTANTS_DIR', 'UTILS_DIR', 
    'LOGS_DIR', 'SYSTEM_PROMPTS_PATH', 'OUTPUT_DIRECTORY', 'LOG_DIR', 'LOG_FILE',
    'FILE_ENCODING', 'FILE_EXTENSIONS',
    'LOG_COLORS', 'LOGGING_LEVEL', 'MAX_LOG_FILE_SIZE', 'BACKUP_COUNT',
    'LOG_TIMESTAMP_FORMAT', 'LOG_FILENAME_TEMPLATE',
    'ERROR_MESSAGES', 'SENSITIVE_PATTERNS',
    'LAST_PAGE_KEY', 'DEFAULT_LAST_PAGE',
    'DEBUG_WORKFLOW', 'ENABLE_BACKUP', 'ENABLE_FORMATTING', 'ENABLE_INTEGRATION',
    'ENABLE_REMOVAL', 'ENABLE_VALIDATION', 'ENABLE_VERSION_CONTROL', 'STRICT_PARSING',
    'CREATE_MISSING_MODULES', 'PRESERVE_FORMATTING', 'USE_WORKSPACE_ROOT',
    'WORKSPACE_ROOT',
    'ConfigManager'
]