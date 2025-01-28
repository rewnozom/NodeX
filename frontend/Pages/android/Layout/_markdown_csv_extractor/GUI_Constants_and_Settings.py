# ./_markdown_csv_extractor/GUI_Constants_and_Settings.py

import os
from pathlib import Path
from typing import Any, Dict, Optional
from PySide6.QtCore import QObject, Signal
import toml
from dataclasses import dataclass

class GuiConstants:
    # Device type configuration
    MOBILE_MODE = True  # Set to False for desktop
    
    # Touch scroll settings
    TOUCH_SCROLL = True if MOBILE_MODE else False
    KINETIC_SCROLLING = True if MOBILE_MODE else False
    SMOOTH_SCROLL = True if MOBILE_MODE else False
    
    # Touch-specific dimensions
    BUTTON_MIN_HEIGHT = 48 if MOBILE_MODE else 32  # Larger touch targets on mobile
    SCROLL_BAR_WIDTH = 0 if MOBILE_MODE else 12    # Hide scrollbar on mobile
    SPACING = 12 if MOBILE_MODE else 8             # Larger spacing on mobile
    
    # Scroll behavior
    SCROLL_SPEED = 50 if MOBILE_MODE else 30
    SCROLL_ANIMATION_DURATION = 300    # ms
    MOMENTUM_DURATION = 1000 if MOBILE_MODE else 0  # ms
    
    # Visual feedback
    TOUCH_FEEDBACK = True if MOBILE_MODE else False
    
    @classmethod
    def get_scroll_stylesheet(cls) -> str:
        return f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            
            QScrollArea QWidget {{
                background-color: transparent;
            }}
            
            QScrollBar:vertical {{
                width: {cls.SCROLL_BAR_WIDTH}px;
                background-color: transparent;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: #666666;
                border-radius: {cls.SCROLL_BAR_WIDTH//2}px;
                min-height: 30px;
            }}
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """


@dataclass
class SettingsData:
    """Data class for storing settings with type hints"""
    paths: Dict[str, str]
    files: Dict[str, list]
    directories: Dict[str, list]
    file_specific: Dict[str, Any]
    output: Dict[str, str]
    metrics: Dict[str, str]
    presets: Dict[str, list]

    def __post_init__(self):
        """Validate and set default values for settings"""
        if not isinstance(self.file_specific, dict):
            self.file_specific = {"use_file_specific": False, "specific_files": []}
        if "use_file_specific" not in self.file_specific:
            self.file_specific["use_file_specific"] = False
        if "specific_files" not in self.file_specific:
            self.file_specific["specific_files"] = []

class SettingsManager(QObject):
    """Manages loading, saving, and updating application settings"""
    settings_changed = Signal()

    def __init__(self, settings_path: str):
        super().__init__()
        self._settings_path = Path(settings_path).resolve()
        self._settings: Optional[SettingsData] = None
        self._load_settings()

    def _create_default_settings(self) -> SettingsData:
        """Create a default settings object"""
        return SettingsData(
            paths={"base_dir": "", "output_dir": ""},
            files={"ignored_extensions": [".exe", ".dll"], "ignored_files": []},
            directories={"ignored_directories": []},
            file_specific={"use_file_specific": False, "specific_files": []},
            output={"markdown_file_prefix": "Full_Project", "csv_file_prefix": "Detailed_Project"},
            metrics={"size_unit": "KB"},
            presets={"preset-1": []}
        )

    def _load_settings(self):
        """Load settings from the TOML file"""
        try:
            if not self._settings_path.exists():
                self._settings = self._create_default_settings()
                self._save_settings()
                return

            with open(self._settings_path, 'r', encoding='utf-8') as file:
                data = toml.load(file)
                self._settings = SettingsData(**data)
                self._normalize_paths()

        except Exception as e:
            print(f"Error loading settings: {e}")
            self._settings = self._create_default_settings()
            self._save_settings()

    def _normalize_paths(self):
        """Normalize all paths in settings"""
        if not self._settings:
            return

        def normalize(value: Any) -> Any:
            if isinstance(value, str) and ('/' in value or '\\' in value):
                return str(Path(value).resolve())
            if isinstance(value, list):
                return [normalize(item) for item in value]
            if isinstance(value, dict):
                return {k: normalize(v) for k, v in value.items()}
            return value

        self._settings.paths = normalize(self._settings.paths)

    def _save_settings(self):
        """Save current settings to the TOML file"""
        if not self._settings:
            return

        try:
            settings_dict = {
                field: getattr(self._settings, field)
                for field in self._settings.__annotations__
            }

            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._settings_path, 'w', encoding='utf-8') as file:
                toml.dump(settings_dict, file)

        except Exception as e:
            print(f"Error saving settings: {e}")

    def get_setting(self, section: str, key: str, default: Any = None) -> Any:
        """Retrieve a specific setting"""
        if not self._settings or not hasattr(self._settings, section):
            return default

        section_dict = getattr(self._settings, section)
        return section_dict.get(key, default)

    def get_section(self, section: str, default: Any = None) -> Any:
        """Get an entire settings section"""
        if not self._settings or not hasattr(self._settings, section):
            return default
        return getattr(self._settings, section)

    def update_setting(self, section: str, key: str, value: Any):
        """Update a specific setting"""
        if not self._settings:
            return

        section_dict = getattr(self._settings, section, {})
        if isinstance(section_dict, dict):
            section_dict[key] = value
            self._save_settings()
            self.settings_changed.emit()

    def remove_setting(self, section: str, key: str):
        """Remove a setting key from a section"""
        if not self._settings or not hasattr(self._settings, section):
            return

        section_dict = getattr(self._settings, section)
        if isinstance(section_dict, dict) and key in section_dict:
            del section_dict[key]
            self._save_settings()
            self.settings_changed.emit()

    # Added Methods for Path Handling
    def absolute_to_relative(self, path: str) -> str:
        """Convert an absolute path to a relative path based on base_dir."""
        base_dir = self.get_setting("paths", "base_dir", "")
        try:
            relative_path = os.path.relpath(path, base_dir)
            return relative_path
        except ValueError:
            return path  # Return as-is if conversion fails

    def relative_to_absolute(self, relative_path: str) -> str:
        """Convert a relative path to an absolute path based on base_dir."""
        base_dir = self.get_setting("paths", "base_dir", "")
        return os.path.abspath(os.path.join(base_dir, relative_path))

