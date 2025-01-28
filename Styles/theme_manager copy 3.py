import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from functools import lru_cache
import logging

from PySide6.QtGui import QPalette, QColor, QBrush, QLinearGradient
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ThemeMetadata:
    """Represents theme metadata"""
    theme_name: str
    version: str
    description: str
    author: str
    last_updated: str

class ThemeLoader:
    """Handles loading and merging of theme JSON files"""
    
    @staticmethod
    def load_theme_directory(theme_path: Path) -> Dict[str, Any]:
        """
        Load and merge all JSON files in a theme directory.
        Files are loaded in alphabetical order to ensure consistent merging.
        """
        theme_data = {}
        
        try:
            # Get all JSON files in the directory and sort them
            json_files = sorted(theme_path.glob("*.json"))
            
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                        # Deep merge the data
                        theme_data = ThemeLoader._deep_merge(theme_data, file_data)
                    logger.info(f"Loaded theme file: {json_file}")
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding {json_file}: {e}")
                except Exception as e:
                    logger.error(f"Error loading {json_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing theme directory {theme_path}: {e}")
            
        return theme_data

    @staticmethod
    def _deep_merge(base: Dict, update: Dict) -> Dict:
        """
        Recursively merge two dictionaries, with update taking precedence
        """
        merged = base.copy()
        
        for key, value in update.items():
            if (
                key in merged and 
                isinstance(merged[key], dict) and 
                isinstance(value, dict)
            ):
                merged[key] = ThemeLoader._deep_merge(merged[key], value)
            else:
                merged[key] = value
                
        return merged



class StylesheetBuilder:
    """Handles generation of Qt stylesheets from theme data"""
    
    def __init__(self, theme_data: Dict[str, Any]):
        self.theme = theme_data
        
    def build_global_stylesheet(self) -> str:
        """Build the global application stylesheet"""
        styles = []
        
        # Add base styles
        styles.append(self._build_base_styles())
        
        # Add component styles
        styles.append(self._build_component_styles())
        
        # Add specialized components
        styles.append(self._build_specialized_styles())
        
        return '\n'.join(styles)
    
    def _build_base_styles(self) -> str:
        """Build base application styles"""
        typography = self.theme.get('TYPOGRAPHY', {})
        base_colors = self.theme.get('BASE', {})
        
        return f"""
            QWidget {{
                font-family: {typography.get('fonts', {}).get('primary', {}).get('family', 'system-ui')};
                font-size: {typography.get('sizes', {}).get('scale', {}).get('base', '16px')};
                color: {base_colors.get('colors', {}).get('text', {}).get('primary', '#000000')};
                background-color: transparent;
            }}
            
            QWidget:disabled {{
                color: {base_colors.get('colors', {}).get('text', {}).get('disabled', '#666666')};
                background-color: transparent;
            }}
        """
    
    def _build_component_styles(self) -> str:
        """Build styles for basic components"""
        components = self.theme.get('COMPONENTS', {})
        styles = []
        
        # Button styles
        button = components.get('button', {})
        styles.append(self._build_button_styles(button))
        
        # Input styles
        input_styles = components.get('input', {})
        styles.append(self._build_input_styles(input_styles))
        
        return '\n'.join(styles)
    
    def _build_button_styles(self, button_config: Dict[str, Any]) -> str:
        """Build button styles"""
        variants = button_config.get('variants', {})
        base = variants.get('primary', {})
        
        return f"""
            QPushButton {{
                background-color: {base.get('background')};
                color: {base.get('color')};
                border: none;
                border-radius: {button_config.get('sizes', {}).get('md', {}).get('borderRadius', '4px')};
                padding: {button_config.get('sizes', {}).get('md', {}).get('padding', '8px 16px')};
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {base.get('hover', {}).get('background')};
            }}
            
            QPushButton:pressed {{
                background-color: {base.get('active', {}).get('background')};
            }}
            
            QPushButton:disabled {{
                background-color: {base.get('disabled', {}).get('background')};
                color: {base.get('disabled', {}).get('color')};
            }}
        """
    
    def _build_input_styles(self, input_config: Dict[str, Any]) -> str:
        """Build input styles"""
        base = input_config.get('base', {})
        states = input_config.get('states', {})
        
        return f"""
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {base.get('background')};
                color: {base.get('color')};
                border: {base.get('border')};
                border-radius: {base.get('borderRadius')};
                padding: {base.get('padding')};
            }}
            
            QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {{
                border: {states.get('hover', {}).get('border')};
            }}
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border: {states.get('focus', {}).get('border')};
                box-shadow: {states.get('focus', {}).get('boxShadow')};
            }}
        """
    
    def _build_specialized_styles(self) -> str:
        """Build styles for specialized components"""
        specialized = self.theme.get('SPECIALIZED_COMPONENTS', {})
        styles = []
        
        # Table styles
        if 'table' in specialized:
            styles.append(self._build_table_styles(specialized['table']))
        
        # Progress bar styles
        if 'progress' in specialized:
            styles.append(self._build_progress_styles(specialized['progress']))
        
        return '\n'.join(styles)
    
    def _build_table_styles(self, table_config: Dict[str, Any]) -> str:
        """Build table styles"""
        return f"""
            QTableView {{
                background-color: {table_config.get('container', {}).get('background')};
                border: {table_config.get('container', {}).get('border')};
                border-radius: {table_config.get('container', {}).get('borderRadius')};
                gridline-color: {table_config.get('row', {}).get('base', {}).get('borderBottom')};
            }}
            
            QHeaderView::section {{
                background-color: {table_config.get('header', {}).get('background')};
                padding: {table_config.get('header', {}).get('cell', {}).get('padding')};
                border-bottom: {table_config.get('header', {}).get('borderBottom')};
                color: {table_config.get('header', {}).get('cell', {}).get('color')};
            }}
        """
    
    def _build_progress_styles(self, progress_config: Dict[str, Any]) -> str:
            """Build progress bar styles"""
            base = progress_config.get('base', {})
            bar = progress_config.get('bar', {})
            
            return f"""
                QProgressBar {{
                    background-color: {base.get('background', 'transparent')};
                    border: none;
                    border-radius: {base.get('borderRadius', '0')};
                    height: {base.get('height', '4px')};
                }}
                
                QProgressBar::chunk {{
                    background-color: {bar.get('background', '#fb923c')};
                    border-radius: {base.get('borderRadius', '0')};
                }}
            """

class WidgetStyleManager:
    """Handles widget-specific styling and updates"""
    
    def __init__(self, theme_data: Dict[str, Any]):
        self.theme = theme_data
        self._style_cache = {}
        
    def apply_widget_style(self, widget: QWidget) -> None:
        """Apply appropriate styling to a specific widget"""
        widget_type = widget.metaObject().className()
        
        # Get cached style or generate new one
        if widget_type not in self._style_cache:
            self._style_cache[widget_type] = self._generate_widget_style(widget_type)
            
        widget.setStyleSheet(self._style_cache[widget_type])
        
        # Apply any widget-specific customizations
        self._apply_widget_customizations(widget)
    
    def _generate_widget_style(self, widget_type: str) -> str:
        """Generate style for a specific widget type"""
        if widget_type == "QDialog":
            return self._generate_dialog_style()
        elif widget_type == "QMainWindow":
            return self._generate_main_window_style()
        elif widget_type == "QTabWidget":
            return self._generate_tab_style()
        elif widget_type == "QScrollBar":
            return self._generate_scrollbar_style()
        
        # Return empty string for unknown widget types
        return ""
    
    def _generate_dialog_style(self) -> str:
        """Generate style for QDialog"""
        dialog = self.theme.get('COMPONENTS', {}).get('dialog', {})
        effects = self.theme.get('BASE', {}).get('effects', {})
        
        return f"""
            QDialog {{
                background: {dialog.get('background', effects.get('glassmorphism', {}).get('background'))};
                border: {dialog.get('border', '1px solid rgba(82, 82, 82, 0.3)')};
                border-radius: {dialog.get('borderRadius', '0.75rem')};
            }}
        """
    
    def _generate_main_window_style(self) -> str:
        """Generate style for QMainWindow"""
        base = self.theme.get('BASE', {})
        
        return f"""
            QMainWindow {{
                background: {base.get('colors', {}).get('background', {}).get('primary')};
            }}
        """
    
    def _generate_tab_style(self) -> str:
        """Generate style for QTabWidget"""
        tabs = self.theme.get('NAVIGATION', {}).get('tabs', {})
        
        return f"""
            QTabWidget::pane {{
                border: {tabs.get('list', {}).get('borderBottom')};
                background: transparent;
            }}
            
            QTabBar::tab {{
                padding: {tabs.get('tab', {}).get('base', {}).get('padding')};
                color: {tabs.get('tab', {}).get('base', {}).get('color')};
                margin-right: 4px;
            }}
            
            QTabBar::tab:selected {{
                color: {tabs.get('tab', {}).get('states', {}).get('selected', {}).get('color')};
                border-bottom: {tabs.get('tab', {}).get('states', {}).get('selected', {}).get('borderBottom')};
            }}
            
            QTabBar::tab:hover:!selected {{
                color: {tabs.get('tab', {}).get('states', {}).get('hover', {}).get('color')};
            }}
        """
    
    def _generate_scrollbar_style(self) -> str:
        """Generate style for QScrollBar"""
        scrollbar = self.theme.get('COMPONENTS', {}).get('scrollbar', {})
        
        return f"""
            QScrollBar:vertical {{
                background: {scrollbar.get('background', 'transparent')};
                width: {scrollbar.get('width', '12px')};
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background: {scrollbar.get('handle', {}).get('background', '#fb923c')};
                min-height: {scrollbar.get('handle', {}).get('minHeight', '20px')};
                border-radius: {scrollbar.get('handle', {}).get('borderRadius', '6px')};
            }}
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background: {scrollbar.get('background', 'transparent')};
                height: {scrollbar.get('width', '12px')};
                margin: 0px;
            }}
            
            QScrollBar::handle:horizontal {{
                background: {scrollbar.get('handle', {}).get('background', '#fb923c')};
                min-width: {scrollbar.get('handle', {}).get('minHeight', '20px')};
                border-radius: {scrollbar.get('handle', {}).get('borderRadius', '6px')};
            }}
            
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """
    
    def _apply_widget_customizations(self, widget: QWidget) -> None:
        """Apply any special customizations for specific widget types"""
        widget_type = widget.metaObject().className()
        
        if widget_type == "QMainWindow":
            self._customize_main_window(widget)
        elif widget_type == "QDialog":
            self._customize_dialog(widget)
            
    def _customize_main_window(self, window: QWidget) -> None:
        """Apply customizations specific to QMainWindow"""
        effects = self.theme.get('BASE', {}).get('effects', {}).get('glassmorphism', {})
        
        window.setAttribute(Qt.WA_TranslucentBackground)
        if effects.get('backdrop_filter'):
            # Note: Backdrop filter support requires additional platform-specific handling
            pass
            
    def _customize_dialog(self, dialog: QWidget) -> None:
        """Apply customizations specific to QDialog"""
        effects = self.theme.get('BASE', {}).get('effects', {})
        
        # Apply shadow if specified
        if shadow := effects.get('shadows', {}).get('lg'):
            # Note: Shadow implementation might require platform-specific handling
            pass

class AnimationManager:
    """Handles theme-based animations"""
    
    def __init__(self, theme_data: Dict[str, Any]):
        self.theme = theme_data
        self.animations = theme_data.get('ANIMATIONS', {})
        
    def get_animation(self, name: str) -> Dict[str, Any]:
        """Get animation configuration by name"""
        return self.animations.get(name, {})
        
    def apply_animation(self, widget: QWidget, animation_name: str) -> None:
        """Apply an animation to a widget"""
        animation_config = self.get_animation(animation_name)
        if not animation_config:
            return
            
        # Implementation for applying animations
        # Note: This would require QPropertyAnimation setup based on the configuration
        pass



from typing import Dict, Any, Optional, List
import json
import os
from pathlib import Path
from dataclasses import dataclass
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class ThemeSource(Enum):
    """Enum for different theme sources"""
    FILE = "file"
    DIRECTORY = "directory"
    MEMORY = "memory"

@dataclass
class ThemeValidationError:
    """Represents a theme validation error"""
    path: str
    message: str
    severity: str

class ThemeValidator:
    """Validates theme configuration"""
    
    REQUIRED_SECTIONS = {
        'BASE': {'colors', 'effects', 'transitions'},
        'TYPOGRAPHY': {'fonts', 'sizes', 'lineHeight'},
        'COMPONENTS': {'button', 'input', 'card'},
        'SPECIALIZED_COMPONENTS': {'tooltip', 'progress', 'table'}
    }
    
    @classmethod
    def validate_theme(cls, theme_data: Dict[str, Any]) -> List[ThemeValidationError]:
        """Validate a theme configuration"""
        errors = []
        
        # Validate required sections
        for section, required_keys in cls.REQUIRED_SECTIONS.items():
            if section not in theme_data:
                errors.append(ThemeValidationError(
                    path=section,
                    message=f"Required section '{section}' is missing",
                    severity="error"
                ))
            else:
                section_data = theme_data[section]
                for key in required_keys:
                    if key not in section_data:
                        errors.append(ThemeValidationError(
                            path=f"{section}.{key}",
                            message=f"Required key '{key}' is missing in section '{section}'",
                            severity="error"
                        ))
        
        # Validate color formats
        errors.extend(cls._validate_colors(theme_data))
        
        return errors
    
    @classmethod
    def _validate_colors(cls, theme_data: Dict[str, Any], path: str = "") -> List[ThemeValidationError]:
        """Recursively validate color values"""
        errors = []
        
        for key, value in theme_data.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(value, dict):
                errors.extend(cls._validate_colors(value, current_path))
            elif isinstance(value, str) and any(
                color_indicator in key.lower() 
                for color_indicator in ['color', 'background', 'border']
            ):
                if not cls._is_valid_color(value):
                    errors.append(ThemeValidationError(
                        path=current_path,
                        message=f"Invalid color format: {value}",
                        severity="error"
                    ))
        
        return errors
    
    @staticmethod
    def _is_valid_color(color: str) -> bool:
        """Validate color format"""
        if color.startswith('#'):
            return len(color) in [4, 7, 9]  # #RGB, #RRGGBB, #RRGGBBAA
        elif color.startswith('rgb'):
            return color.startswith('rgb(') or color.startswith('rgba(')
        return False

class ThemeConfig:
    """Handles theme configuration and settings"""
    
    def __init__(self, config_path: str = "./config/theme_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load theme configuration"""
        default_config = {
            "theme_directories": ["./themes"],
            "default_theme": "dark",
            "fallback_theme": "light",
            "cache_themes": True,
            "validate_themes": True
        }
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    return {**default_config, **loaded_config}
        except Exception as e:
            logger.error(f"Error loading theme config: {e}")
        
        return default_config
    
    def save_config(self) -> bool:
        """Save current configuration"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving theme config: {e}")
            return False
    
    def get_theme_directories(self) -> List[str]:
        """Get configured theme directories"""
        return self.config.get("theme_directories", ["./themes"])
    
    def get_default_theme(self) -> str:
        """Get default theme name"""
        return self.config.get("default_theme", "dark")

class ThemeCache:
    """Handles caching of theme data"""
    
    def __init__(self, cache_dir: str = "./cache/themes"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cached_theme(self, theme_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve theme from cache"""
        cache_file = self.cache_dir / f"{theme_name}.json"
        
        try:
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error reading theme cache: {e}")
        
        return None
    
    def cache_theme(self, theme_name: str, theme_data: Dict[str, Any]) -> bool:
        """Cache theme data"""
        cache_file = self.cache_dir / f"{theme_name}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(theme_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error caching theme: {e}")
            return False
    
    def clear_cache(self) -> None:
        """Clear theme cache"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
        except Exception as e:
            logger.error(f"Error clearing theme cache: {e}")

class ThemeDirectory:
    """Handles theme directory structure and organization"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self._ensure_structure()
    
    def _ensure_structure(self) -> None:
        """Ensure proper theme directory structure"""
        try:
            # Create base directories
            (self.base_path / "dark").mkdir(parents=True, exist_ok=True)
            (self.base_path / "light").mkdir(parents=True, exist_ok=True)
            
            # Create readme if it doesn't exist
            readme_path = self.base_path / "README.md"
            if not readme_path.exists():
                with open(readme_path, 'w') as f:
                    f.write("""# Theme Directory Structure
                    
Each theme should be organized in its own directory with multiple JSON files:
- base.json (colors, effects, transitions)
- typography.json (fonts, sizes, spacing)
- components.json (basic UI components)
- specialized.json (complex components)
- animations.json (animations and transitions)
""")
        except Exception as e:
            logger.error(f"Error ensuring theme directory structure: {e}")
    
    def list_themes(self) -> List[str]:
        """List available themes"""
        try:
            return [
                d.name for d in self.base_path.iterdir()
                if d.is_dir() and not d.name.startswith('_')
            ]
        except Exception as e:
            logger.error(f"Error listing themes: {e}")
            return []
    
    def get_theme_path(self, theme_name: str) -> Optional[Path]:
        """Get path for a specific theme"""
        theme_path = self.base_path / theme_name
        return theme_path if theme_path.is_dir() else None


class ThemeManager:
    """
    Enhanced Theme Manager that handles multiple JSON files per theme
    """
    _instance = None
    _themes: Dict[str, Dict[str, Any]] = {}
    _current_theme: Optional[Dict[str, Any]] = None
    _current_theme_name: Optional[str] = None
    
    def __new__(cls, config_path: str = "./config/theme_config.json"):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            cls._instance._initialize(config_path)
        return cls._instance
    
    def _initialize(self, config_path: str) -> None:
        """Initialize the theme manager"""
        # Basic initialization
        self._registered_widgets = set()
        self._theme_metadata = {}
        
        # Initialize managers
        self._style_builder = None
        self._widget_style_manager = None
        self._animation_manager = None
        
        # Initialize configuration and cache
        self.config = ThemeConfig(config_path)
        self.cache = ThemeCache()
        self.validator = ThemeValidator()
        self._theme_directories = [
            ThemeDirectory(path) 
            for path in self.config.get_theme_directories()
        ]
        
        # Load default theme if specified
        default_theme = self.config.get_default_theme()
        if default_theme:
            self.apply_theme(default_theme)
    
    def discover_themes(self, themes_root: str = "./themes") -> None:
        """
        Discover and load all themes from the themes directory.
        Each subdirectory is treated as a separate theme.
        """
        themes_path = Path(themes_root)
        
        if not themes_path.exists():
            logger.error(f"Themes root directory not found: {themes_root}")
            return
            
        # Clear existing themes
        self._themes.clear()
        self._theme_metadata.clear()
        
        # Discover theme directories
        for theme_dir in themes_path.iterdir():
            if theme_dir.is_dir() and not theme_dir.name.startswith('_'):
                try:
                    # Load and merge all JSON files in the theme directory
                    theme_data = ThemeLoader.load_theme_directory(theme_dir)
                    
                    if theme_data:
                        theme_name = theme_dir.name
                        self._themes[theme_name] = theme_data
                        
                        # Extract metadata if available
                        if '__metadata__' in theme_data:
                            metadata = theme_data['__metadata__']
                            self._theme_metadata[theme_name] = ThemeMetadata(
                                theme_name=metadata.get('theme_name', theme_name),
                                version=metadata.get('version', '1.0.0'),
                                description=metadata.get('description', ''),
                                author=metadata.get('author', 'Unknown'),
                                last_updated=metadata.get('last_updated', '')
                            )
                            
                        logger.info(f"Loaded theme: {theme_name}")
                        
                except Exception as e:
                    logger.error(f"Error loading theme from {theme_dir}: {e}")
    
    def load_theme(self, theme_name: str) -> Optional[Dict[str, Any]]:
        """Load a theme by name"""
        # Try cache first
        if self.config.config.get("cache_themes"):
            cached_theme = self.cache.get_cached_theme(theme_name)
            if cached_theme:
                return cached_theme
        
        # Search in theme directories
        theme_data = None
        for theme_dir in self._theme_directories:
            if theme_path := theme_dir.get_theme_path(theme_name):
                theme_data = ThemeLoader.load_theme_directory(theme_path)
                break
        
        if theme_data:
            # Validate if configured
            if self.config.config.get("validate_themes"):
                errors = self.validator.validate_theme(theme_data)
                if errors:
                    for error in errors:
                        logger.warning(f"Theme validation: {error.path} - {error.message}")
            
            # Cache theme
            if self.config.config.get("cache_themes"):
                self.cache.cache_theme(theme_name, theme_data)
            
            return theme_data
        
        return None
    
    def apply_theme(self, theme_name: str) -> None:
        """Apply a theme to the application"""
        if theme_name not in self._themes:
            logger.error(f"Theme '{theme_name}' not found")
            return
            
        try:
            theme = self._themes[theme_name]
            self._current_theme = theme
            self._current_theme_name = theme_name
            
            # Initialize managers
            self._initialize_managers()
            
            # Apply the theme
            self._apply_palette(theme)
            
            # Apply global stylesheet
            if self._style_builder:
                stylesheet = self._style_builder.build_global_stylesheet()
                QApplication.instance().setStyleSheet(stylesheet)
            
            # Update registered widgets
            self._update_registered_widgets()
            
            logger.info(f"Applied theme: {theme_name}")
            
        except Exception as e:
            logger.error(f"Error applying theme {theme_name}: {e}")
    
    def _initialize_managers(self) -> None:
        """Initialize style and animation managers"""
        if self._current_theme:
            self._style_builder = StylesheetBuilder(self._current_theme)
            self._widget_style_manager = WidgetStyleManager(self._current_theme)
            self._animation_manager = AnimationManager(self._current_theme)
    
    def register_widget(self, widget: QWidget) -> None:
        """Register a widget for theme updates"""
        self._registered_widgets.add(widget)
        if self._current_theme and self._widget_style_manager:
            self._widget_style_manager.apply_widget_style(widget)
    
    def _update_registered_widgets(self) -> None:
        """Update all registered widgets with the current theme"""
        if self._widget_style_manager:
            for widget in self._registered_widgets:
                if widget.isWidgetType():
                    self._widget_style_manager.apply_widget_style(widget)
    
    def _apply_palette(self, theme: Dict[str, Any]) -> None:
        """Apply color palette to the application"""
        try:
            palette = QPalette()
            base_colors = theme.get('BASE', {}).get('colors', {})
            
            # Set window colors
            palette.setColor(QPalette.Window, self._parse_color(base_colors.get('background', {}).get('primary')))
            palette.setColor(QPalette.WindowText, self._parse_color(base_colors.get('text', {}).get('primary')))
            
            # Set widget colors
            palette.setColor(QPalette.Base, self._parse_color(base_colors.get('background', {}).get('secondary')))
            palette.setColor(QPalette.AlternateBase, self._parse_color(base_colors.get('background', {}).get('tertiary')))
            palette.setColor(QPalette.Text, self._parse_color(base_colors.get('text', {}).get('primary')))
            
            # Set highlight colors
            accent_colors = base_colors.get('accent', {})
            palette.setColor(QPalette.Highlight, self._parse_color(accent_colors.get('primary')))
            palette.setColor(QPalette.HighlightedText, self._parse_color(base_colors.get('text', {}).get('inverse')))
            
            QApplication.instance().setPalette(palette)
            
        except Exception as e:
            logger.error(f"Error applying palette: {e}")
    
    @staticmethod
    def _parse_color(color_str: str) -> QColor:
        """Parse color string to QColor"""
        if not color_str:
            return QColor("#000000")
            
        try:
            if color_str.startswith('rgba'):
                values = color_str.strip('rgba()').split(',')
                return QColor(
                    int(values[0]),
                    int(values[1]),
                    int(values[2]),
                    int(float(values[3]) * 255)
                )
            return QColor(color_str)
        except Exception as e:
            logger.error(f"Error parsing color {color_str}: {e}")
            return QColor("#000000")
    
    def get_available_themes(self) -> List[str]:
        """Get list of available themes"""
        themes = set()
        for theme_dir in self._theme_directories:
            themes.update(theme_dir.list_themes())
        return sorted(list(themes))
    
    def clear_cache(self) -> None:
        """Clear theme cache"""
        self.cache.clear_cache()