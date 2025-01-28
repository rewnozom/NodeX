# settings/settings_manager.py

import toml
from pathlib import Path
from typing import Dict, Any, Optional
from PySide6.QtCore import QObject, Signal
from dataclasses import dataclass
from .settings_data import SettingsData
from Utils.Paths.paths import normalize, normalize_settings_paths, ensure_directory, _normalize_paths

@dataclass
class SettingsManager(QObject):
    """Optimized Settings Manager with signals for PySide6"""
    
    settings_changed = Signal()  # Signal emitted when settings are modified
    
    def __init__(self, settings_path: str = "./settings/settings.toml"):
        super().__init__()
        self._settings_path = Path(settings_path).resolve()
        self._settings: Optional[SettingsData] = None
        self._load_settings()

    def _create_default_settings(self) -> SettingsData:
        """Create default settings structure"""
        return SettingsData()  # Uses default values from dataclass

    def _load_settings(self) -> None:
        """Load settings with error handling and path normalization"""
        try:
            if not self._settings_path.exists():
                self._settings = self._create_default_settings()
                self._save_settings()
                return

            with self._settings_path.open('r', encoding='utf-8') as f:
                content = f.read().replace('\\', '/')
                data = toml.loads(content)
                
            # Convert loaded data to SettingsData
            self._settings = SettingsData(**data)
            # Use the imported _normalize_paths function
            _normalize_paths(self._settings)
            
        except Exception as e:
            print(f"Error loading settings: {e}")
            self._settings = self._create_default_settings()
            self._save_settings()

        # Normalize paths after loading
        if self._settings and hasattr(self._settings, 'paths'):
            self._settings.paths = normalize(self._settings.paths)

    def _save_settings(self) -> None:
        """Save settings with proper path handling"""
        if not self._settings:
            return
                
        try:
            # Ensure directory exists
            ensure_directory(self._settings_path.parent)
            
            # Convert SettingsData to dict using to_dict method
            settings_dict = self._settings.to_dict()
            
            # Use enhanced path normalization
            normalized_settings = normalize_settings_paths(settings_dict)
            
            with self._settings_path.open('w', encoding='utf-8') as f:
                toml.dump(normalized_settings, f)
                    
        except Exception as e:
            print(f"Error saving settings: {e}")

    def update_setting(self, section: str, key: str, value: Any) -> None:
        """Update a setting value, create it if missing, and emit change signal"""
        if not self._settings:
            return

        # Access or create the section dictionary
        section_dict = getattr(self._settings, section, None)
        if section_dict is None:
            section_dict = {}
            setattr(self._settings, section, section_dict)

        # Check if the key exists in the section dictionary
        if isinstance(section_dict, dict):
            if key not in section_dict:
                # Create a new preset if it doesn't exist
                section_dict[key] = value if isinstance(value, list) else [value]
            elif isinstance(section_dict[key], list) and isinstance(value, list):
                # Append items to an existing list if `value` is a list
                section_dict[key].extend(v for v in value if v not in section_dict[key])
            else:
                section_dict[key] = value

            # Save the updated settings to the file
            self._save_settings()
            self.settings_changed.emit()
        else:
            print(f"Section '{section}' is not a dictionary or does not exist in settings.")

    def get_setting(self, section: str, key: str, default: Any = None) -> Any:
        """Retrieve a specific setting or return a default value."""
        if not self._settings or not hasattr(self._settings, section):
            return default
        section_data = getattr(self._settings, section)
        if isinstance(section_data, dict):
            return section_data.get(key, default)
        return default
    
    def get_section(self, section: str, default: Any = None) -> Any:
        """Retrieve an entire settings section or return a default value."""
        if not self._settings or not hasattr(self._settings, section):
            return default
        return getattr(self._settings, section)
    
    def remove_setting(self, section: str, key: str) -> None:
        """Remove a setting key from a section, save changes, and emit change signal"""
        if not self._settings or not hasattr(self._settings, section):
            return

        section_dict = getattr(self._settings, section)
        if isinstance(section_dict, dict) and key in section_dict:
            del section_dict[key]
            self._save_settings()
            self.settings_changed.emit()

    @property
    def settings(self) -> Optional[SettingsData]:
        """Property to access settings data"""
        return self._settings