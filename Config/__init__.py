# ./setting/__init__.py

from .AppConfig.config import (
    APP_NAME,
    VERSION,
    DEBUG_MODE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    DEFAULT_WINDOW_SIZE,
    THEME_DARK,
    THEME_LIGHT,
    CURRENT_THEME,
    THEME_OPTIONS,
    DEFAULT_THEME,
    ANDROID_LAYOUT_DIR,  # Uppdaterad konstant
    DESKTOP_LAYOUT_DIR,  # Uppdaterad konstant
    COMPANY_NAME,
    APPLICATION_NAME,
    LAST_PAGE_KEY,
    DEFAULT_LAST_PAGE,
    ERROR_MESSAGES,
    ENABLE_PHONE_LAYOUT,
    SENSITIVE_PATTERNS,
    LOG_DIR,
    MAX_LOG_FILE_SIZE,
    BACKUP_COUNT,
    LOGGING_LEVEL,
)

from .AppConfig.icon_config import (
    ICON_PATH,
    ICONS,
    ICON_NAMES,
)

# Define __all__ to specify what should be imported when using 'from setting import *'
__all__ = [
    # Application Configuration
    "APP_NAME",
    "VERSION",
    "DEBUG_MODE",
    "WINDOW_WIDTH",
    "WINDOW_HEIGHT",
    "DEFAULT_WINDOW_SIZE",
    
    # Theme Configuration
    "THEME_DARK",
    "THEME_LIGHT",
    "CURRENT_THEME",
    "THEME_OPTIONS",
    "DEFAULT_THEME",
    
    # Directory Configuration
    "ANDROID_LAYOUT_DIR",  # Uppdaterad konstant
    "DESKTOP_LAYOUT_DIR",  # Uppdaterad konstant
    
    # Application Identity
    "COMPANY_NAME",
    "APPLICATION_NAME",
    
    # Settings and Features
    "LAST_PAGE_KEY",
    "DEFAULT_LAST_PAGE",
    "ENABLE_PHONE_LAYOUT",
    "ERROR_MESSAGES",
    
    # Logging Configuration
    "SENSITIVE_PATTERNS",
    "LOG_DIR",
    "MAX_LOG_FILE_SIZE",
    "BACKUP_COUNT",
    "LOGGING_LEVEL",
    
    # Icon Configuration
    "ICON_PATH",
    "ICONS",
    "ICON_NAMES",
]
