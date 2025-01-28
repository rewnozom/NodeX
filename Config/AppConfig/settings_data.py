# settings/settings_data.py

from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class SettingsData:
    """Data structure for application settings with type hints and default values"""
    paths: Dict[str, str] = field(default_factory=lambda: {
        "base_dir": "",
        "output_dir": ""
    })
    
    files: Dict[str, List[str]] = field(default_factory=lambda: {
        "ignored_extensions": [".exe", ".dll"],
        "ignored_files": ["file_to_ignore.txt"]
    })
    
    directories: Dict[str, List[str]] = field(default_factory=lambda: {
        "ignored_directories": ["dir_to_ignore"]
    })
    
    file_specific: Dict[str, Any] = field(default_factory=lambda: {
        "use_file_specific": False,
        "specific_files": [""]
    })
    
    output: Dict[str, str] = field(default_factory=lambda: {
        "markdown_file_prefix": "Full_Project",
        "csv_file_prefix": "Detailed_Project"
    })
    
    metrics: Dict[str, str] = field(default_factory=lambda: {
        "size_unit": "KB"
    })
    
    presets: Dict[str, List[str]] = field(default_factory=lambda: {
        "preset-1": [""]
    })

    def to_dict(self) -> Dict[str, Any]:
        """Convert the settings data class to a dictionary for saving."""
        return {
            "paths": self.paths,
            "files": self.files,
            "directories": self.directories,
            "file_specific": self.file_specific,
            "output": self.output,
            "metrics": self.metrics,
            "presets": self.presets,
        }