from pathlib import Path
from typing import Union, Any, Dict

def normalize(value: Any) -> Any:
    """Original normalize function from SettingsManager, enhanced with Path type support"""
    if isinstance(value, (str, Path)) and ('/' in str(value) or '\\' in str(value)):
        return str(Path(value).resolve())
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()}
    return value

def _normalize_paths(settings) -> None:
    """Original _normalize_paths method from SettingsManager, enhanced with settings dictionary support"""
    if not settings:
        return
    
    if isinstance(settings, dict):
        return normalize_settings_paths(settings)
    
    # Original behavior for SettingsData object
    settings.paths = normalize(settings.paths)
    return settings

def normalize_path(value: Union[str, Path]) -> str:
    """Normalize a path string or Path object to a resolved string path"""
    if isinstance(value, (str, Path)) and ('/' in str(value) or '\\' in str(value)):
        return str(Path(value).resolve())
    return str(value)

def normalize_settings_paths(settings_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced version that works with both dictionary and SettingsData objects"""
    return normalize(settings_dict)

def ensure_directory(path: Union[str, Path]) -> None:
    """Utility function to ensure directory exists"""
    Path(path).mkdir(parents=True, exist_ok=True)