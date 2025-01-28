# -*- coding: utf-8 -*-
# ./gui.py

from extractorz import ExtractorWorker, ReverseCSVEx, ReverseMarkdownEx, MarkdownEx, CSVEx

import os
import toml
import shutil
from typing import Dict, Any, Optional, List
from PySide6.QtCore import QObject, Signal, Qt, QTimer, QThread, Slot, QThreadPool
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
from threading import Lock
from PySide6.QtGui import QColor, QPalette, QFont, QKeyEvent
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QPushButton, QLabel, 
    QComboBox, QSpacerItem, QSizePolicy, QScrollArea, QWidget, 
    QLineEdit, QGridLayout, QFileDialog, QHBoxLayout, QListWidget,
    QMessageBox, QInputDialog, QProgressBar, QSlider, QButtonGroup,
    QApplication, QMainWindow, QCheckBox, QTabWidget, QTextEdit
)

from PySide6.QtCore import QEvent
from PySide6.QtGui import QColor, QPalette, QFont, QKeyEvent


class ResourceManager:
    """Centralized resource management for better memory handling"""
    def __init__(self):
        self._resources = {}
        self._cleanup_hooks = []

    def register_resource(self, key: str, resource: any, cleanup_hook=None):
        """Register a resource with optional cleanup"""
        self._resources[key] = resource
        if cleanup_hook:
            self._cleanup_hooks.append((key, cleanup_hook))

    def get_resource(self, key: str) -> any:
        """Get a registered resource"""
        return self._resources.get(key)

    def cleanup(self):
        """Clean up all registered resources"""
        for key, hook in self._cleanup_hooks:
            try:
                if key in self._resources:
                    hook(self._resources[key])
            except Exception as e:
                print(f"Error cleaning up resource {key}: {e}")
        self._resources.clear()
        self._cleanup_hooks.clear()


# Custom ListWidget with keyPressed signal
class CustomListWidget(QListWidget):
    keyPressed = Signal(QKeyEvent)

    def keyPressEvent(self, event: QKeyEvent):
        self.keyPressed.emit(event)
        super().keyPressEvent(event)

class ThemeColors(Enum):
    PRIMARY = "#212121"
    SECONDARY_BACKGROUND = "#424242"
    PRIMARY_BUTTONS = "#B71C1C"
    HOVER_BUTTONS = "#D32F2F"
    TEXT_PRIMARY = "#d4d4d4"
    TERTIARY = "#424242"

class AppTheme:
    """Central theme management for the application"""
    
    @staticmethod
    def get_base_stylesheet():
        return f"""
            QWidget {{
                background-color: {ThemeColors.PRIMARY.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                font-family: 'Segoe UI', sans-serif;
            }}
            
            QPushButton {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                color: {ThemeColors.TEXT_PRIMARY.value};
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {ThemeColors.HOVER_BUTTONS.value};
            }}
            
            QPushButton:pressed {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
            }}
            
            QScrollBar:vertical {{
                border: none;
                background: {ThemeColors.PRIMARY.value};
                width: 14px;
                margin: 15px 0 15px 0;
                border-radius: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                min-height: 30px;
                border-radius: 7px;
            }}
            
            QLineEdit {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                padding: 5px;
                border-radius: 4px;
                color: {ThemeColors.TEXT_PRIMARY.value};
            }}
            
            QComboBox {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 4px;
                padding: 5px;
                min-width: 6em;
            }}
        """

    @staticmethod
    def apply_theme(app):
        """Apply the theme to the entire application"""
        app.setStyle("Fusion")
        
        # Set application-wide stylesheet
        app.setStyleSheet(AppTheme.get_base_stylesheet())
        
        # Set up dark palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(ThemeColors.PRIMARY.value))
        palette.setColor(QPalette.WindowText, QColor(ThemeColors.TEXT_PRIMARY.value))
        palette.setColor(QPalette.Base, QColor(ThemeColors.SECONDARY_BACKGROUND.value))
        palette.setColor(QPalette.AlternateBase, QColor(ThemeColors.PRIMARY.value))
        palette.setColor(QPalette.ToolTipBase, QColor(ThemeColors.TEXT_PRIMARY.value))
        palette.setColor(QPalette.ToolTipText, QColor(ThemeColors.TEXT_PRIMARY.value))
        palette.setColor(QPalette.Text, QColor(ThemeColors.TEXT_PRIMARY.value))
        palette.setColor(QPalette.Button, QColor(ThemeColors.PRIMARY_BUTTONS.value))
        palette.setColor(QPalette.ButtonText, QColor(ThemeColors.TEXT_PRIMARY.value))
        palette.setColor(QPalette.Link, QColor(ThemeColors.HOVER_BUTTONS.value))
        palette.setColor(QPalette.Highlight, QColor(ThemeColors.HOVER_BUTTONS.value))
        palette.setColor(QPalette.HighlightedText, QColor(ThemeColors.TEXT_PRIMARY.value))
        
        app.setPalette(palette)

class Fonts:
    """Central font management"""
    
    @staticmethod
    def get_default(size=10, weight=QFont.Normal):
        font = QFont("Segoe UI", size)
        font.setWeight(weight)
        return font
    
    @staticmethod
    def get_bold(size=10):
        return Fonts.get_default(size, QFont.Bold)



class ExtractionWorker(QObject):
    """Worker class for handling extractions in a separate thread"""
    finished = Signal()
    error = Signal(str)
    progress = Signal(int)
    status = Signal(str)

    def __init__(self, extractor_class, input_path, output_path, settings_path):
        """
        Initialize the worker with extraction parameters.
        """
        super().__init__()
        self.extractor_class = extractor_class
        self.input_path = input_path
        self.output_path = output_path
        self.settings_path = settings_path
        self._extractor = None
        self._is_running = True
        self._lock = Lock()

    def run(self):
        """
        Main execution method that runs in a separate thread.
        """
        try:
            # Create the extractor instance
            self._extractor = self.extractor_class(
                self.input_path,
                self.output_path,
                self.settings_path
            )

            print(f"ExtractionWorker: Starting extraction with {self._extractor.__class__.__name__}")
            
            if not self._is_running:
                print("ExtractionWorker: Process stopped before starting")
                return

            # Connect progress and status signals
            if hasattr(self._extractor, 'update_progress'):
                self._extractor.update_progress = lambda value: self._safe_emit_progress(value)
            if hasattr(self._extractor, 'update_status'):
                self._extractor.update_status = lambda msg: self._safe_emit_status(msg)

            # Run the extraction
            if self._is_running:
                self._extractor.run()
                print("ExtractionWorker: Extraction completed successfully")
                self.finished.emit()

        except Exception as e:
            print(f"ExtractionWorker: Error during extraction: {str(e)}")
            self.error.emit(str(e))
        finally:
            self._cleanup()

    def _safe_emit_progress(self, value: int):
        """
        Thread-safe progress emission.
        
        Args:
            value: Progress value between 0 and 100
        """
        with self._lock:
            if self._is_running:
                try:
                    self.progress.emit(value)
                except Exception as e:
                    print(f"ExtractionWorker: Error emitting progress: {str(e)}")

    def _safe_emit_status(self, message: str):
        """
        Thread-safe status message emission.
        
        Args:
            message: Status message to emit
        """
        with self._lock:
            if self._is_running:
                try:
                    self.status.emit(message)
                except Exception as e:
                    print(f"ExtractionWorker: Error emitting status: {str(e)}")

    def stop(self):
        """
        Properly stop the worker and cleanup.
        This method is thread-safe.
        """
        print("ExtractionWorker: Stop requested")
        with self._lock:
            self._is_running = False
            if self._extractor and hasattr(self._extractor, 'stop'):
                try:
                    self._extractor.stop()
                except Exception as e:
                    print(f"ExtractionWorker: Error stopping extractor: {str(e)}")

    def _cleanup(self):
        """
        Cleanup resources and ensure proper shutdown.
        This method is called in the finally block of run().
        """
        with self._lock:
            try:
                self._is_running = False
                if self._extractor and hasattr(self._extractor, 'cleanup'):
                    self._extractor.cleanup()
                self._extractor = None
                print("ExtractionWorker: Cleanup completed")
            except Exception as e:
                print(f"ExtractionWorker: Error during cleanup: {str(e)}")

    def isRunning(self) -> bool:
        """
        Thread-safe method to check if the worker is still running.
        
        Returns:
            bool: True if the worker is still running, False otherwise
        """
        with self._lock:
            return self._is_running



class ExtractionManager(QObject):
    """Improved extraction manager with better thread handling"""
    all_finished = Signal()
    extraction_error = Signal(str)

    def __init__(self):
        super().__init__()
        self._active_workers = {}
        self._lock = Lock()
        self._error_count = 0

    def start_extraction(self, extraction_type: str, worker: ExtractionWorker):
        """Start a new extraction with proper thread management"""
        with self._lock:
            # Cleanup any existing extraction of same type
            self.stop_extraction(extraction_type)

            # Create and setup new thread
            thread = QThread()
            worker.moveToThread(thread)

            # Store worker and thread
            self._active_workers[extraction_type] = (worker, thread)

            # Connect signals
            thread.started.connect(worker.run)
            worker.finished.connect(lambda: self._handle_extraction_finished(extraction_type))
            worker.error.connect(lambda err: self._handle_extraction_error(extraction_type, err))
            
            # Cleanup connections
            worker.finished.connect(thread.quit)
            thread.finished.connect(thread.deleteLater)
            worker.finished.connect(worker.deleteLater)

            # Start thread
            thread.start()

    def stop_extraction(self, extraction_type: str):
        """Stop specific extraction with cleanup"""
        with self._lock:
            if extraction_type in self._active_workers:
                worker, thread = self._active_workers[extraction_type]
                worker.stop()
                thread.quit()
                thread.wait()  # Wait for thread to finish
                self._active_workers.pop(extraction_type)

    def stop_all(self):
        """Stop all extractions and cleanup"""
        with self._lock:
            for extraction_type in list(self._active_workers.keys()):
                self.stop_extraction(extraction_type)

    def _handle_extraction_finished(self, extraction_type: str):
        """Handle successful extraction completion"""
        with self._lock:
            if extraction_type in self._active_workers:
                self._active_workers.pop(extraction_type)
            
            if not self._active_workers and self._error_count == 0:
                self.all_finished.emit()

    def _handle_extraction_error(self, extraction_type: str, error_msg: str):
        """Handle extraction error"""
        with self._lock:
            self._error_count += 1
            if extraction_type in self._active_workers:
                self._active_workers.pop(extraction_type)
            self.extraction_error.emit(f"{extraction_type}: {error_msg}")

    def is_running(self, extraction_type: str = None) -> bool:
        """Check if specific or any extraction is running"""
        with self._lock:
            if extraction_type:
                return extraction_type in self._active_workers
            return bool(self._active_workers)

    def get_active_extractions(self) -> list:
        """Get list of currently running extractions"""
        with self._lock:
            return list(self._active_workers.keys())


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

class SettingsManager(QObject):
    """Optimized Settings Manager with signals for PySide6"""
    
    settings_changed = Signal()  # Signal emitted when settings are modified
    
    def __init__(self, settings_path: str):
        super().__init__()
        self._settings_path = Path(settings_path).resolve()
        self._settings: Optional[SettingsData] = None
        self._load_settings()
    
    def _create_default_settings(self) -> SettingsData:
        """Create default settings structure"""
        return SettingsData(
            paths={"base_dir": "", "output_dir": ""},
            files={
                "ignored_extensions": [".exe", ".dll"],
                "ignored_files": ["file_to_ignore.txt"]
            },
            directories={"ignored_directories": ["dir_to_ignore"]},
            file_specific={
                "use_file_specific": False,
                "specific_files": [""]
            },
            output={
                "markdown_file_prefix": "Full_Project",
                "csv_file_prefix": "Detailed_Project"
            },
            metrics={"size_unit": "KB"},
            presets={"preset-1": [""]}
        )
    
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
            self._normalize_paths()
            
        except Exception as e:
            print(f"Error loading settings: {e}")
            self._settings = self._create_default_settings()
            self._save_settings()
    
    def _normalize_paths(self) -> None:
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
        # Normalize other relevant sections...
    
    def _save_settings(self) -> None:
        """Save settings with proper path handling"""
        if not self._settings:
            return
            
        try:
            # Ensure directory exists
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert SettingsData to dict and save
            settings_dict = {
                field: getattr(self._settings, field)
                for field in self._settings.__annotations__
            }
            
            with self._settings_path.open('w', encoding='utf-8') as f:
                toml.dump(settings_dict, f)
                
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

    @property
    def settings_path(self) -> str:
        """Expose the settings path as a read-only property."""
        return str(self._settings_path)

    @property
    def settings(self) -> Optional[SettingsData]:
        """Property to access settings data"""
        return self._settings

    def get_setting(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """Safely get a setting value or entire section if key is None"""
        if not self._settings or not hasattr(self._settings, section):
            return default

        section_dict = getattr(self._settings, section)
        if key is None:
            return section_dict
        return section_dict.get(key, default)
    
    def get_section(self, section: str, default: Any = None) -> Any:
        """Retrieve the entire section dictionary"""
        if not self._settings or not hasattr(self._settings, section):
            return default
        return getattr(self._settings, section)
    
    def remove_setting(self, section: str, key: str) -> None:
        """Remove a setting key from a section, save changes, and emit change signal"""
        if not self._settings or not hasattr(self._settings, section):
            return

        section_dict = getattr(self._settings, section)
        if isinstance(section_dict, dict) and key in section_dict:
            del section_dict[key]  # Remove the specified key from the section dictionary
            self._save_settings()  # Save changes to the settings file
            self.settings_changed.emit()  # Emit signal to notify other components


class SettingsManager(QObject):
    """Optimized Settings Manager with signals for PySide6"""
    
    settings_changed = Signal()  # Signal emitted when settings are modified
    
    def __init__(self, settings_path: str):
        super().__init__()
        self._settings_path = Path(settings_path).resolve()
        self._settings: Optional[SettingsData] = None
        self._load_settings()

    @property
    def settings_path(self) -> str:
        """Expose the settings path as a read-only property."""
        return str(self._settings_path)

    def _create_default_settings(self) -> SettingsData:
        """Create default settings structure"""
        return SettingsData(
            paths={"base_dir": "", "output_dir": ""},
            files={
                "ignored_extensions": [".exe", ".dll"],
                "ignored_files": ["file_to_ignore.txt"]
            },
            directories={"ignored_directories": ["dir_to_ignore"]},
            file_specific={
                "use_file_specific": False,
                "specific_files": [""]
            },
            output={
                "markdown_file_prefix": "Full_Project",
                "csv_file_prefix": "Detailed_Project"
            },
            metrics={"size_unit": "KB"},
            presets={"preset-1": [""]}
        )

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
            self._normalize_paths()
            
        except Exception as e:
            print(f"Error loading settings: {e}")
            self._settings = self._create_default_settings()
            self._save_settings()

    def _normalize_paths(self) -> None:
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
        # Normalize other relevant sections...

    def _save_settings(self) -> None:
        """Save settings with proper path handling"""
        if not self._settings:
            return
            
        try:
            # Ensure directory exists
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert SettingsData to dict and save
            settings_dict = {
                field: getattr(self._settings, field)
                for field in self._settings.__annotations__
            }
            
            with self._settings_path.open('w', encoding='utf-8') as f:
                toml.dump(settings_dict, f)
                
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

    @property
    def settings(self) -> Optional[SettingsData]:
        """Property to access settings data"""
        return self._settings

    def get_setting(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """Safely get a setting value or entire section if key is None"""
        if not self._settings or not hasattr(self._settings, section):
            return default

        section_dict = getattr(self._settings, section)
        if key is None:
            return section_dict
        return section_dict.get(key, default)
    
    def get_section(self, section: str, default: Any = None) -> Any:
        """Retrieve the entire section dictionary"""
        if not self._settings or not hasattr(self._settings, section):
            return default
        return getattr(self._settings, section)
    
    def remove_setting(self, section: str, key: str) -> None:
        """Remove a setting key from a section, save changes, and emit change signal"""
        if not self._settings or not hasattr(self._settings, section):
            return

        section_dict = getattr(self._settings, section)
        if isinstance(section_dict, dict) and key in section_dict:
            del section_dict[key]  # Remove the specified key from the section dictionary
            self._save_settings()  # Save changes to the settings file
            self.settings_changed.emit()  # Emit signal to notify other components



class SidebarButton(QPushButton):
    """Custom styled sidebar button"""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFont(Fonts.get_default(10))
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.PRIMARY.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                padding: 10px;
                text-align: left;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
            }}
            QPushButton:disabled {{
                background-color: {ThemeColors.PRIMARY.value};
                color: #666666;
                border: 1px solid #333333;
            }}
        """)

class ThemeComboBox(QComboBox):
    """Custom styled combo box for theme selections"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(Fonts.get_default(9))
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                padding: 5px;
                border-radius: 4px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: url(resources/arrow-down.png);
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                selection-background-color: {ThemeColors.PRIMARY_BUTTONS.value};
            }}
        """)

class SidebarFrame(QFrame):
    # Signals for theme and scaling changes
    appearance_mode_changed = Signal(str)
    scaling_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarFrame")
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Initialize and setup the UI components"""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 20, 10, 20)
        self.layout.setSpacing(10)
        
        # Logo/Title
        self.logo_label = QLabel("extractor")
        self.logo_label.setFont(Fonts.get_bold(20))
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.logo_label)
        
        
        # Add vertical spacer
        self.layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        
        # Appearance mode section
        self.appearance_label = QLabel("Appearance Mode:")
        self.appearance_label.setFont(Fonts.get_default(9))
        self.layout.addWidget(self.appearance_label)
        
        self.appearance_mode_combo = ThemeComboBox()
        self.appearance_mode_combo.addItems(["Light", "Dark", "System"])
        self.appearance_mode_combo.setCurrentText("Dark")
        self.layout.addWidget(self.appearance_mode_combo)
        
        # UI Scaling section
        self.scaling_label = QLabel("UI Scaling:")
        self.scaling_label.setFont(Fonts.get_default(9))
        self.layout.addWidget(self.scaling_label)
        
        self.scaling_combo = ThemeComboBox()
        self.scaling_combo.addItems(["80%", "90%", "100%", "110%", "120%"])
        self.scaling_combo.setCurrentText("100%")
        self.layout.addWidget(self.scaling_combo)
        
        # Set fixed width for sidebar
        self.setFixedWidth(200)
        
        # Apply frame styling
        self.setStyleSheet(f"""
            QFrame#sidebarFrame {{
                background-color: {ThemeColors.PRIMARY.value};
                border-right: 1px solid {ThemeColors.TERTIARY.value};
            }}
            QLabel {{
                color: {ThemeColors.TEXT_PRIMARY.value};
            }}
        """)

    def setup_connections(self):
        """Setup signal connections"""
        # Remove the incorrect radiobutton connection since radiobutton_frame doesn't exist in SidebarFrame
        self.appearance_mode_combo.currentTextChanged.connect(
            self.change_appearance_mode_event
        )
        
        self.scaling_combo.currentTextChanged.connect(
            self.change_scaling_event
        )

    def sidebar_button_event(self, button_index: int):
        """Handle sidebar button clicks"""
        print(f"Sidebar button {button_index + 1} clicked")
        # Emit custom signal or handle the event as needed

    def change_appearance_mode_event(self, new_appearance_mode: str):
        """Handle appearance mode changes"""
        self.appearance_mode_changed.emit(new_appearance_mode)
        # You might want to update the theme here
        
    def change_scaling_event(self, new_scaling: str):
        """Handle UI scaling changes"""
        try:
            scaling_float = float(new_scaling.replace("%", "")) / 100
            self.scaling_changed.emit(str(scaling_float))
            # Implement the actual scaling logic here
        except ValueError:
            print(f"Invalid scaling value: {new_scaling}")

    def add_custom_button(self, text: str, callback) -> SidebarButton:
        """Add a new custom button to the sidebar"""
        btn = SidebarButton(text)
        btn.clicked.connect(callback)
        # Insert before the spacer
        self.layout.insertWidget(len(self.buttons), btn)
        self.buttons.append(btn)
        return btn

    def remove_button(self, button: SidebarButton):
        """Remove a button from the sidebar"""
        if button in self.buttons:
            self.buttons.remove(button)
            self.layout.removeWidget(button)
            button.deleteLater()

@dataclass
class SettingWidgetGroup:
    """Data class to keep track of related widgets for each setting"""
    label: QLabel
    editor: QLineEdit
    buttons: Optional[list] = None

class ScrollableTextboxFrame(QFrame):

    setting_changed = Signal(str, str, str)  # section, key, value
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.widget_groups: Dict[str, Dict[str, SettingWidgetGroup]] = {}
        self.setup_ui()
        
        # Connect to settings manager signals
        self.settings_manager.settings_changed.connect(self.refresh_settings)
        
        # Delayed initialization of settings
        QTimer.singleShot(100, self.load_settings_to_ui)

    def setup_ui(self):
        """Initialize the UI components"""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Scroll Area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {ThemeColors.PRIMARY.value};
            }}
            QScrollBar:vertical {{
                background-color: {ThemeColors.PRIMARY.value};
                width: 12px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                min-height: 30px;
                border-radius: 6px;
                margin: 2px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        # Content Widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        
        self.scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll_area)

    def create_setting_widgets(self, section: str, key: str, value: Any) -> SettingWidgetGroup:
        """Create widgets for a setting entry"""
        # Section header if needed
        if section not in self.widget_groups:
            self.widget_groups[section] = {}
            header = QLabel(section.capitalize())
            header.setFont(Fonts.get_bold(12))
            self.content_layout.addWidget(header)

        # Setting container
        container = QWidget()
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 5, 0, 5)
        
        # Label
        label = QLabel(key)
        label.setFont(Fonts.get_default(10))
        
        # Editor
        editor = QLineEdit()
        editor.setFont(Fonts.get_default(10))
        if isinstance(value, list):
            editor.setText(", ".join(str(v) for v in value))
        else:
            editor.setText(str(value))
            
        editor.textChanged.connect(
            lambda text, s=section, k=key: self.handle_setting_changed(s, k, text)
        )

        layout.addWidget(label, 0, 0)
        layout.addWidget(editor, 0, 1)

        buttons = []
        if key in ["ignored_files", "skip_paths"]:
            # Add file/folder buttons
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            
            add_file_btn = QPushButton("Add File")
            add_file_btn.clicked.connect(
                lambda checked, s=section, k=key: self.add_file_to_setting(s, k)
            )
            
            add_folder_btn = QPushButton("Add Folder")
            add_folder_btn.clicked.connect(
                lambda checked, s=section, k=key: self.add_folder_to_setting(s, k)
            )
            
            buttons = [add_file_btn, add_folder_btn]
            btn_layout.addWidget(add_file_btn)
            btn_layout.addWidget(add_folder_btn)
            layout.addWidget(btn_container, 1, 0, 1, 2)

        self.content_layout.addWidget(container)
        return SettingWidgetGroup(label=label, editor=editor, buttons=buttons)

    def load_settings_to_ui(self):
        """Load settings into the UI with lazy loading for better performance"""
        if not self.settings_manager.settings:
            return

        # Define the order of sections explicitly
        ordered_sections = [
            "paths", "files", "directories", "file_specific",
            "output", "metrics", "presets"
        ]

        def load_section(section_name: str, settings: dict):
            for key, value in settings.items():
                if section_name not in self.widget_groups or key not in self.widget_groups[section_name]:
                    widget_group = self.create_setting_widgets(section_name, key, value)
                    self.widget_groups[section_name][key] = widget_group
                else:
                    # Update existing widgets
                    widget_group = self.widget_groups[section_name][key]
                    if isinstance(value, list):
                        widget_group.editor.setText(", ".join(str(v) for v in value))
                    else:
                        widget_group.editor.setText(str(value))

        # Load each section according to the specified order
        for section in ordered_sections:
            settings = getattr(self.settings_manager.settings, section, None)
            if settings:
                load_section(section, settings)

    def handle_setting_changed(self, section: str, key: str, value: str):
        """Handle changes to settings values"""
        if hasattr(self.settings_manager.settings, section):
            section_dict = getattr(self.settings_manager.settings, section)
            if key in section_dict:
                if isinstance(section_dict[key], list):
                    new_value = [v.strip() for v in value.split(",") if v.strip()]
                else:
                    new_value = value
                self.setting_changed.emit(section, key, value)
                self.settings_manager.update_setting(section, key, new_value)

    def add_file_to_setting(self, section: str, key: str):
        """Add a file to a list setting"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            self.settings_manager.get_setting("paths", "base_dir", "")
        )
        if file_path:
            base_dir = self.settings_manager.get_setting("paths", "base_dir", "")
            relative_path = os.path.relpath(file_path, base_dir)
            current_value = self.widget_groups[section][key].editor.text()
            new_value = f"{current_value}, {relative_path}" if current_value else relative_path
            self.widget_groups[section][key].editor.setText(new_value)

    def add_folder_to_setting(self, section: str, key: str):
        """Add a folder to a list setting"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            self.settings_manager.get_setting("paths", "base_dir", "")
        )
        if folder_path:
            base_dir = self.settings_manager.get_setting("paths", "base_dir", "")
            relative_path = os.path.relpath(folder_path, base_dir)
            current_value = self.widget_groups[section][key].editor.text()
            new_value = f"{current_value}, {relative_path}" if current_value else relative_path
            self.widget_groups[section][key].editor.setText(new_value)

    def refresh_settings(self):
        """Refresh the UI when settings change"""
        self.load_settings_to_ui()

class TabViewFrame(QFrame):
    preset_changed = Signal(str, list)  # preset_name, files
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()
        self.setup_connections()
        
        # Load initial preset files on launch
        initial_preset = self.preset_combo.currentText()
        if initial_preset:
            self.load_preset_files(initial_preset)

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(20)
        
        # Settings Frame
        self.settings_frame = QFrame(self)
        self.settings_frame.setObjectName("SettingsFrame")
        self.setup_settings_frame()
        self.layout.addWidget(self.settings_frame)
        
        # File Specific Frame
        self.file_specific_frame = QFrame(self)
        self.file_specific_frame.setObjectName("FileSpecificFrame")
        self.setup_file_specific_frame()
        self.layout.addWidget(self.file_specific_frame)

        # Styling for Settings and File Specific Frames
        self.setStyleSheet(f"""
            QFrame#SettingsFrame, QFrame#FileSpecificFrame {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 4px;
            }}
            QLabel {{
                color: {ThemeColors.TEXT_PRIMARY.value};
            }}
            QPushButton {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.HOVER_BUTTONS.value};
            }}
            QPushButton:pressed {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
            }}
        """)

    def setup_settings_frame(self):
        """Setup the Settings frame"""
        layout = QVBoxLayout(self.settings_frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("Settings")
        header.setFont(Fonts.get_bold(14))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # File Specific Toggle
        self.use_file_specific_combo = QComboBox()
        self.use_file_specific_combo.addItems(["True", "False"])
        current_setting = self.settings_manager.get_setting("file_specific", "use_file_specific", False)
        self.use_file_specific_combo.setCurrentText(str(current_setting))
        layout.addWidget(QLabel("Enable File Specific:"))
        layout.addWidget(self.use_file_specific_combo)
        
        # Add File/Folder Buttons
        self.add_file_button = QPushButton("Add File")
        self.add_folder_button = QPushButton("Add Folder")
        self.choose_output_button = QPushButton("Choose Output Directory")
        
        layout.addWidget(self.add_file_button)
        layout.addWidget(self.add_folder_button)
        layout.addWidget(self.choose_output_button)
        
        layout.addStretch()

    def setup_file_specific_frame(self):
        """Setup the File Specific frame"""
        layout = QVBoxLayout(self.file_specific_frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("File Specific")
        header.setFont(Fonts.get_bold(14))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # File List using CustomListWidget
        self.file_listbox = CustomListWidget()
        self.file_listbox.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(QLabel("File List:"))
        layout.addWidget(self.file_listbox)
        
        # Preset Controls
        self.preset_combo = QComboBox()
        presets = self.settings_manager.get_section("presets", default={})
        self.preset_combo.addItems(presets.keys())
        layout.addWidget(QLabel("Presets:"))
        layout.addWidget(self.preset_combo)
        
        # Preset Buttons
        self.add_preset_button = QPushButton("Add Preset")
        self.remove_preset_button = QPushButton("Remove Preset")
        layout.addWidget(self.add_preset_button)
        layout.addWidget(self.remove_preset_button)
        
        layout.addStretch()

    def setup_connections(self):
        """Setup signal connections"""

        # File Specific Frame Connections
        self.preset_combo.currentTextChanged.connect(self.load_preset_files)
        self.add_preset_button.clicked.connect(self.add_preset)
        self.remove_preset_button.clicked.connect(self.remove_preset)

        # Settings Frame Connections
        self.use_file_specific_combo.currentTextChanged.connect(self.change_use_file_specific)
        self.add_file_button.clicked.connect(self.add_files)
        self.add_folder_button.clicked.connect(self.add_folder)
        self.choose_output_button.clicked.connect(self.choose_output_directory)
        

        
        # Connect the custom keyPressed signal
        self.file_listbox.keyPressed.connect(self.handle_key_press)

    def change_use_file_specific(self, value: str):
        """Handle changes to use_file_specific setting"""
        self.settings_manager.update_setting(
            'file_specific', 
            'use_file_specific', 
            value == "True"
        )

    def load_preset_files(self, preset_name: str):
        """Load files for selected preset"""
        if not preset_name:
            return
        
        self.file_listbox.clear()
        preset_files = self.settings_manager.get_setting(
            "presets", 
            preset_name, 
            []
        )
        self.file_listbox.addItems(preset_files)

    def add_preset(self):
        """Add a new preset"""
        name, ok = QInputDialog.getText(
            self,
            "Preset Name",
            "Enter the name for the new preset:"
        )
        if ok and name:
            self.settings_manager.update_setting("presets", name, [])
            self.preset_combo.addItem(name)
            self.preset_combo.setCurrentText(name)
            self.load_preset_files(name)

    def remove_preset(self):
        """Remove the selected preset with a Yes/No confirmation dialog"""
        preset_name = self.preset_combo.currentText()
        if not preset_name:
            return

        # Show confirmation dialog
        confirmation = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove the preset '{preset_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        # If user confirms, proceed with removal
        if confirmation == QMessageBox.Yes:
            self.settings_manager.remove_setting("presets", preset_name)
            self.preset_combo.removeItem(self.preset_combo.findText(preset_name))
            self.file_listbox.clear()
            self.preset_changed.emit(preset_name, [])

    def add_files(self):
        """Add files to the current preset"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            self.settings_manager.get_setting("paths", "base_dir", "")
        )
        
        if files:
            self._add_files_to_preset(files)

    def add_folder(self):
        """Add all files from a folder to the current preset"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            self.settings_manager.get_setting("paths", "base_dir", "")
        )
        
        if folder:
            files = []
            for root, _, filenames in os.walk(folder):
                for filename in filenames:
                    files.append(os.path.join(root, filename))
            
            self._add_files_to_preset(files)

    def _add_files_to_preset(self, files: List[str]):
        """Helper method to add files to current preset"""
        preset_name = self.preset_combo.currentText()
        if not preset_name:
            QMessageBox.warning(
                self,
                "No Preset Selected",
                "Please select a preset to add files to."
            )
            return
            
        base_dir = self.settings_manager.get_setting("paths", "base_dir", "")
        preset_files = self.settings_manager.get_setting("presets", preset_name, [])
        
        for file_path in files:
            relative_path = os.path.relpath(file_path, base_dir)
            if relative_path not in preset_files:
                preset_files.append(relative_path)
        
        self.settings_manager.update_setting("presets", preset_name, preset_files)
        self.load_preset_files(preset_name)
        self.preset_changed.emit(preset_name, preset_files)

    def choose_output_directory(self):
        """Choose output directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Choose Output Directory",
            self.settings_manager.get_setting("paths", "output_dir", "")
        )
        
        if directory:
            self.settings_manager.update_setting("paths", "output_dir", directory)

    def handle_key_press(self, event: QKeyEvent):
        """Handle key press events in the file list"""
        if event.key() == Qt.Key_Delete:
            self.remove_selected_files()

    def remove_selected_files(self):
        """Remove selected files from the current preset"""
        preset_name = self.preset_combo.currentText()
        if not preset_name:
            return
            
        selected_items = self.file_listbox.selectedItems()
        if not selected_items:
            return
            
        preset_files = self.settings_manager.get_setting("presets", preset_name, [])
        for item in selected_items:
            file_path = item.text()
            if file_path in preset_files:
                preset_files.remove(file_path)
        
        self.settings_manager.update_setting("presets", preset_name, preset_files)
        self.load_preset_files(preset_name)
        self.preset_changed.emit(preset_name, preset_files)



class SegmentedButton(QPushButton):
    """Custom segmented button implementation"""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setFont(Fonts.get_default(10))
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                padding: 8px 16px;
            }}
            QPushButton:checked {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.HOVER_BUTTONS.value};
            }}
        """)

class CustomProgressBar(QProgressBar):
    """Enhanced progress bar with custom styling"""
    def __init__(self, parent=None, orientation=Qt.Horizontal):
        super().__init__(parent)
        self.setOrientation(orientation)
        self.setStyleSheet(f"""
            QProgressBar {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 3px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
                border-radius: 2px;
            }}
        """)

class CustomSlider(QSlider):
    """Enhanced slider with custom styling"""
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 6px;
                background: {ThemeColors.SECONDARY_BACKGROUND.value};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {ThemeColors.PRIMARY_BUTTONS.value};
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QSlider::groove:vertical {{
                width: 6px;
                background: {ThemeColors.SECONDARY_BACKGROUND.value};
                border-radius: 3px;
            }}
            QSlider::handle:vertical {{
                background: {ThemeColors.PRIMARY_BUTTONS.value};
                height: 18px;
                margin: 0 -6px;
                border-radius: 9px;
            }}
        """)

class SliderProgressbarFrame(QFrame):
    progress_changed = Signal(float)  # Value between 0 and 1
    segment_changed = Signal(str)     # Selected segment value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
        
        # Start indeterminate progress
        self.start_progress_animation()

    def setup_ui(self):
        """Initialize the UI components"""
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Segmented button group
        self.button_layout = QHBoxLayout()
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        
        segments = ["Value 1", "Value 2", "Value 3"]
        for i, text in enumerate(segments):
            btn = SegmentedButton(text)
            self.button_layout.addWidget(btn)
            self.button_group.addButton(btn, i)
            if i == 1:  # Set default selection to "Value 2"
                btn.setChecked(True)
        
        self.layout.addLayout(self.button_layout)
        
        # Progress bars
        self.progress_bar1 = CustomProgressBar()
        self.progress_bar2 = CustomProgressBar()
        self.layout.addWidget(self.progress_bar1)
        self.layout.addWidget(self.progress_bar2)
        
        # Horizontal slider
        self.slider_h = CustomSlider(Qt.Horizontal)
        self.slider_h.setRange(0, 100)
        self.slider_h.setValue(50)
        self.layout.addWidget(self.slider_h)
        
        # Integrate ScrollableFrame with "99" switches
        self.scrollable_switches = ScrollableFrame(self)
        self.layout.addWidget(self.scrollable_switches)
        
        # Vertical slider and vertical progress bar
        self.vertical_layout = QHBoxLayout()
        
        self.slider_v = CustomSlider(Qt.Vertical)
        self.slider_v.setRange(0, 100)
        self.slider_v.setValue(50)
        self.vertical_layout.addWidget(self.slider_v)
        
        self.progress_bar3 = CustomProgressBar(orientation=Qt.Vertical)
        self.progress_bar3.setTextVisible(False)
        self.vertical_layout.addWidget(self.progress_bar3)
        
        self.layout.addLayout(self.vertical_layout)
        
        # Apply frame styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.PRIMARY.value};
                border: none;
            }}
        """)

    def setup_connections(self):
        """Setup signal connections"""
        self.button_group.buttonClicked.connect(self.handle_segment_changed)
        self.slider_h.valueChanged.connect(self.handle_horizontal_slider)
        self.slider_v.valueChanged.connect(self.handle_vertical_slider)
        
        # Connect switch state changes if needed
        for switch in self.scrollable_switches.switches:
            switch.stateChanged.connect(self.handle_switch_state_change)

    def handle_segment_changed(self, button: SegmentedButton):
        """Handle segment button selection"""
        self.segment_changed.emit(button.text())

    def handle_horizontal_slider(self, value: int):
        """Handle horizontal slider value change"""
        normalized_value = value / 100.0
        self.progress_bar2.setValue(value)
        self.progress_changed.emit(normalized_value)

    def handle_vertical_slider(self, value: int):
        """Handle vertical slider value change"""
        self.progress_bar3.setValue(value)

    def handle_switch_state_change(self, state: int):
        """Handle switch (checkbox) state changes"""
        sender = self.sender()
        if isinstance(sender, QCheckBox):
            print(f"{sender.text()} toggled to {'Checked' if state == Qt.Checked else 'Unchecked'}")
            # Implement any additional logic based on switch state

    def start_progress_animation(self):
        """Start the indeterminate progress animation"""
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_indeterminate_progress)
        self.progress_timer.start(50)  # Update every 50ms
        self.progress_value = 0

    def stop_progress_animation(self):
        """Stop the indeterminate progress animation"""
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()

    def update_indeterminate_progress(self):
        """Update the indeterminate progress bar"""
        self.progress_value = (self.progress_value + 2) % 100
        self.progress_bar1.setValue(self.progress_value)

    def set_progress(self, value: float):
        """Set the progress bar values externally"""
        int_value = int(value * 100)
        self.progress_bar2.setValue(int_value)
        self.slider_h.setValue(int_value)
        
    def get_current_segment(self) -> str:
        """Get the currently selected segment"""
        button = self.button_group.checkedButton()
        return button.text() if button else ""


class CustomButton(QPushButton):
    """Custom styled button for the radio frame"""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFont(Fonts.get_default(10))
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                padding: 10px 20px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.HOVER_BUTTONS.value};
            }}
            QPushButton:pressed {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
            }}
        """)

class RadiobuttonFrame(QFrame):
    """Frame for handling reverse extraction operations"""
    
    # Signal definitions
    csv_file_selected = Signal(str)
    csv_output_selected = Signal(str)
    markdown_file_selected = Signal(str)
    markdown_output_selected = Signal(str)
    reverse_csv_triggered = Signal()
    reverse_markdown_triggered = Signal()
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        """Initialize with settings manager"""
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.selected_paths = {}
        self.setup_ui()
        self.setup_connections()
        self.load_saved_paths()

    def setup_ui(self):
        """Initialize the UI components"""
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        self.header_label = QLabel("Reverse Extraction:")
        self.header_label.setFont(Fonts.get_bold(12))
        self.layout.addWidget(self.header_label)
        
        # CSV Controls
        self.select_csv_button = CustomButton("Select CSV File")
        self.select_csv_output_button = CustomButton("Select CSV Output Directory")
        self.reverse_csv_button = CustomButton("Reverse CSV Extraction")
        
        self.layout.addWidget(self.select_csv_button)
        self.layout.addWidget(self.select_csv_output_button)
        self.layout.addWidget(self.reverse_csv_button)
        
        # Markdown Controls
        self.select_markdown_button = CustomButton("Select Markdown File")
        self.select_markdown_output_button = CustomButton("Select Markdown Output Directory")
        self.reverse_markdown_button = CustomButton("Reverse Markdown Extraction")
        
        self.layout.addWidget(self.select_markdown_button)
        self.layout.addWidget(self.select_markdown_output_button)
        self.layout.addWidget(self.reverse_markdown_button)
        
        self.layout.addStretch()
        
        # Frame styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.PRIMARY.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 4px;
            }}
            QLabel {{
                color: {ThemeColors.TEXT_PRIMARY.value};
            }}
        """)

    def setup_connections(self):
        """Setup signal connections with improved error handling"""
        try:
            # Connect button clicks to their handlers
            self.select_csv_button.clicked.connect(self.open_file_dialog_csv)
            self.select_csv_output_button.clicked.connect(self.open_directory_dialog_csv)
            self.reverse_csv_button.clicked.connect(self.handle_reverse_csv)
            
            self.select_markdown_button.clicked.connect(self.open_file_dialog_markdown)
            self.select_markdown_output_button.clicked.connect(self.open_directory_dialog_markdown)
            self.reverse_markdown_button.clicked.connect(self.handle_reverse_markdown)
            
            # Connect reverse extraction signals to their handlers
            self.reverse_csv_triggered.connect(self.handle_reverse_csv)
            self.reverse_markdown_triggered.connect(self.handle_reverse_markdown)
            
            # Connect file operation signals
            self.csv_file_selected.connect(lambda path: self.handle_file_selected('csv', path))
            self.csv_output_selected.connect(lambda path: self.handle_output_selected('csv', path))
            self.markdown_file_selected.connect(lambda path: self.handle_file_selected('markdown', path))
            self.markdown_output_selected.connect(lambda path: self.handle_output_selected('markdown', path))
            
        except Exception as e:
            print(f"Error setting up RadiobuttonFrame connections: {str(e)}")
            QMessageBox.critical(
                self,
                "Connection Error",
                f"An error occurred while setting up connections:\n{str(e)}"
            )

    def load_saved_paths(self):
        """Load saved paths from settings_manager and populate selected_paths."""
        if not self.settings_manager:
            return
        
        csv_file = self.settings_manager.get_setting('paths', 'select_csv_reverse_file', '')
        csv_output = self.settings_manager.get_setting('paths', 'select_csv_output_reverse_dir', '')
        markdown_file = self.settings_manager.get_setting('paths', 'select_markdown_reverse_file', '')
        markdown_output = self.settings_manager.get_setting('paths', 'select_markdown_output_reverse_dir', '')
        
        if csv_file:
            self.selected_paths['csv_file'] = csv_file
        if csv_output:
            self.selected_paths['csv_output'] = csv_output
        if markdown_file:
            self.selected_paths['markdown_file'] = markdown_file
        if markdown_output:
            self.selected_paths['markdown_output'] = markdown_output


    def handle_file_selected(self, type_: str, path: str):
        """Handle file selection with validation"""
        try:
            print(f"Handling file selection - Type: {type_}, Path: {path}")
            if os.path.exists(path):
                self.selected_paths[f'{type_}_file'] = path
                print(f"File path saved for {type_}: {path}")
            else:
                raise FileNotFoundError(f"Selected {type_} file not found: {path}")
        except Exception as e:
            print(f"Error handling file selection: {str(e)}")
            QMessageBox.critical(
                self,
                "File Selection Error",
                f"An error occurred while selecting the {type_} file:\n{str(e)}"
            )
            
    def handle_output_selected(self, type_: str, path: str):
        """Handle output directory selection with validation"""
        try:
            print(f"Handling output selection - Type: {type_}, Path: {path}")
            if os.path.isdir(path) or os.access(os.path.dirname(path), os.W_OK):
                self.selected_paths[f'{type_}_output'] = path
                print(f"Output path saved for {type_}: {path}")
            else:
                raise PermissionError(f"Cannot write to selected {type_} output directory: {path}")
        except Exception as e:
            print(f"Error handling output selection: {str(e)}")
            QMessageBox.critical(
                self,
                "Output Selection Error",
                f"An error occurred while selecting the {type_} output directory:\n{str(e)}"
            )

    def open_file_dialog_csv(self):
        """Open file dialog for CSV selection with settings persistence"""
        print("Opening CSV file dialog")
        base_dir = self.settings_manager.get_setting("paths", "base_dir", "")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            base_dir,
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if file_path:
            print(f"CSV file selected: {file_path}")
            self.selected_paths['csv_file'] = file_path
            if self.settings_manager:
                self.settings_manager.update_setting('paths', 'select_csv_reverse_file', file_path)
            self.csv_file_selected.emit(file_path)

    def handle_reverse_csv(self):
        """Handle reverse CSV extraction"""
        print("Starting reverse CSV extraction")
        paths = self.get_selected_paths()
        csv_file = paths.get('csv_file')
        csv_output = paths.get('csv_output')
        
        if not csv_file or not csv_output:
            QMessageBox.warning(
                self,
                "Missing Paths",
                "Please ensure both CSV file and output directory are selected."
            )
            return
            
        self.reverse_csv_button.setEnabled(False)
        print(f"Processing CSV extraction - Input: {csv_file}, Output: {csv_output}")
        
        try:
            # Create extractor instance first
            extractor = ReverseCSVEx(csv_file, csv_output)
            
            # Create worker and thread
            self.csv_reverse_thread = QThread()
            self.csv_reverse_worker = ExtractionWorker(extractor)
            
            # Move worker to thread
            self.csv_reverse_worker.moveToThread(self.csv_reverse_thread)
            
            # Connect signals
            self.csv_reverse_thread.started.connect(self.csv_reverse_worker.run)
            
            # Connect cleanup signals
            self.csv_reverse_worker.finished.connect(self.csv_reverse_thread.quit)
            self.csv_reverse_worker.finished.connect(self.csv_reverse_worker.deleteLater)
            self.csv_reverse_thread.finished.connect(self.csv_reverse_thread.deleteLater)
            self.csv_reverse_thread.finished.connect(
                lambda: self.reverse_csv_button.setEnabled(True)
            )
            
            # Connect status, progress and error signals
            self.csv_reverse_worker.progress.connect(self.update_reverse_csv_progress)
            self.csv_reverse_worker.status.connect(self.update_reverse_csv_status)
            self.csv_reverse_worker.error.connect(self.on_reverse_csv_error)
            self.csv_reverse_worker.finished.connect(self.on_reverse_csv_finished)
            
            # Start thread
            self.csv_reverse_thread.start()
            print("CSV extraction thread started")
            
        except Exception as e:
            self.reverse_csv_button.setEnabled(True)
            print(f"Error starting CSV extraction: {str(e)}")
            QMessageBox.critical(
                self,
                "Extraction Error",
                f"Failed to start reverse CSV extraction:\n{str(e)}"
            )

    def handle_reverse_markdown(self):
        """Handle reverse Markdown extraction"""
        print("Starting reverse Markdown extraction")
        paths = self.get_selected_paths()
        markdown_file = paths.get('markdown_file')
        markdown_output = paths.get('markdown_output')
        
        # Convert output_path from list to string if needed
        if isinstance(markdown_output, list):
            markdown_output = markdown_output[0] if markdown_output else ""
                
        if not markdown_file or not markdown_output:
            QMessageBox.warning(
                self,
                "Missing Paths",
                "Please ensure both Markdown file and output directory are selected."
            )
            return
        
        self.reverse_markdown_button.setEnabled(False)
        print(f"Processing Markdown extraction - Input: {markdown_file}, Output: {markdown_output}")
        
        try:
            # Create extractor instance
            extractor = ReverseMarkdownEx(
                markdown_file,
                markdown_output,
                self.settings_manager.settings_path
            )
            
            # Create thread first
            self.markdown_reverse_thread = QThread()
            
            # Create worker and move to thread
            self.markdown_reverse_worker = ExtractionWorker(extractor)
            self.markdown_reverse_worker.moveToThread(self.markdown_reverse_thread)
            
            # Connect signals before moving to thread
            self.markdown_reverse_worker.progress.connect(
                self.update_reverse_markdown_progress,
                Qt.QueuedConnection
            )
            self.markdown_reverse_worker.status.connect(
                self.update_reverse_markdown_status,
                Qt.QueuedConnection
            )
            self.markdown_reverse_worker.error.connect(
                self.on_reverse_markdown_error,
                Qt.QueuedConnection
            )
            self.markdown_reverse_worker.finished.connect(
                self.on_reverse_markdown_finished,
                Qt.QueuedConnection
            )
            
            # Thread management signals
            self.markdown_reverse_thread.started.connect(
                self.markdown_reverse_worker.run,
                Qt.QueuedConnection
            )
            self.markdown_reverse_worker.finished.connect(
                self.markdown_reverse_thread.quit,
                Qt.QueuedConnection
            )
            self.markdown_reverse_worker.finished.connect(
                lambda: self.reverse_markdown_button.setEnabled(True),
                Qt.QueuedConnection
            )
            self.markdown_reverse_thread.finished.connect(
                self.markdown_reverse_thread.deleteLater,
                Qt.QueuedConnection
            )
            self.markdown_reverse_worker.finished.connect(
                self.markdown_reverse_worker.deleteLater,
                Qt.QueuedConnection
            )
            
            # Start thread
            print("Starting Markdown extraction thread...")
            self.markdown_reverse_thread.start()
            
        except Exception as e:
            self.reverse_markdown_button.setEnabled(True)
            print(f"Error starting Markdown extraction: {str(e)}")
            QMessageBox.critical(
                self,
                "Extraction Error",
                f"Failed to start reverse Markdown extraction:\n{str(e)}"
            )

    # Progress and status update methods
    def update_reverse_csv_progress(self, value: int):
        """Update the reverse CSV extraction progress"""
        print(f"CSV Progress: {value}%")
        if hasattr(self.parent(), 'entry_run_frame'):
            self.parent().entry_run_frame.csv_progress.setValue(value)

    def update_reverse_csv_status(self, message: str):
        """Update the reverse CSV extraction status"""
        print(f"CSV Status: {message}")
        if hasattr(self.parent(), 'entry_run_frame'):
            self.parent().entry_run_frame.csv_status.setText(message)

    def update_reverse_markdown_progress(self, value: int):
        """Update the reverse Markdown extraction progress"""
        print(f"Markdown Progress: {value}%")
        if hasattr(self.parent(), 'entry_run_frame'):
            self.parent().entry_run_frame.markdown_progress.setValue(value)

    def update_reverse_markdown_status(self, message: str):
        """Update the reverse Markdown extraction status"""
        print(f"Markdown Status: {message}")
        if hasattr(self.parent(), 'entry_run_frame'):
            self.parent().entry_run_frame.markdown_status.setText(message)

    # Completion handlers
    def on_reverse_csv_finished(self):
        """Handle completion of reverse CSV extraction"""
        print("CSV extraction completed")
        if hasattr(self.parent(), 'entry_run_frame'):
            self.parent().entry_run_frame.csv_group.hide()
        QMessageBox.information(
            self,
            "Extraction Complete",
            f"CSV extraction completed successfully.\nOutput Directory: {self.get_selected_paths().get('csv_output')}"
        )

    def on_reverse_markdown_finished(self):
        """Handle completion of reverse Markdown extraction"""
        print("Markdown extraction completed")
        if hasattr(self.parent(), 'entry_run_frame'):
            self.parent().entry_run_frame.markdown_group.hide()
        QMessageBox.information(
            self,
            "Extraction Complete",
            f"Markdown extraction completed successfully.\nOutput Directory: {self.get_selected_paths().get('markdown_output')}"
        )

    # Error handlers
    def on_reverse_csv_error(self, error_message: str):
        """Handle errors in reverse CSV extraction"""
        print(f"CSV extraction error: {error_message}")
        if hasattr(self.parent(), 'entry_run_frame'):
            self.parent().entry_run_frame.csv_group.hide()
        QMessageBox.critical(
            self,
            "Extraction Error",
            f"An error occurred during reverse CSV extraction:\n{error_message}"
        )

    def on_reverse_markdown_error(self, error_message: str):
        """Handle errors in reverse Markdown extraction"""
        print(f"Markdown extraction error: {error_message}")
        if hasattr(self.parent(), 'entry_run_frame'):
            self.parent().entry_run_frame.markdown_group.hide()
        QMessageBox.critical(
            self,
            "Extraction Error",
            f"An error occurred during reverse Markdown extraction:\n{error_message}"
        )

    def open_directory_dialog_csv(self):
        """Open directory dialog for CSV output with settings persistence"""
        print("Opening CSV output directory dialog")
        initial_dir = ""
        if self.settings_manager:
            saved_dir = self.settings_manager.get_setting('paths', 'select_csv_output_reverse_dir', '')
            initial_dir = saved_dir[0] if isinstance(saved_dir, list) else saved_dir
        
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select CSV Output Directory",
            initial_dir
        )
        
        if directory:
            print(f"CSV output directory selected: {directory}")
            self.selected_paths['csv_output'] = directory
            if self.settings_manager:
                self.settings_manager.update_setting('paths', 'select_csv_output_reverse_dir', directory)
            self.csv_output_selected.emit(directory)

    def open_file_dialog_markdown(self):
        """Open file dialog for Markdown selection with settings persistence"""
        print("Opening Markdown file dialog")
        base_dir = self.settings_manager.get_setting("paths", "base_dir", "")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Markdown File",
            base_dir,
            "Markdown Files (*.md);;All Files (*)"
        )
        
        if file_path:
            print(f"Markdown file selected: {file_path}")
            self.selected_paths['markdown_file'] = file_path
            if self.settings_manager:
                self.settings_manager.update_setting('paths', 'select_markdown_reverse_file', file_path)
            self.markdown_file_selected.emit(file_path)

    def open_directory_dialog_markdown(self):
        """Open directory dialog for Markdown output with settings persistence"""
        print("Opening Markdown output directory dialog")
        initial_dir = ""
        if self.settings_manager:
            saved_dir = self.settings_manager.get_setting('paths', 'select_markdown_output_reverse_dir', '')
            # Konvertera från lista till sträng om det behövs
            initial_dir = saved_dir[0] if isinstance(saved_dir, list) else saved_dir
        
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Markdown Output Directory",
            initial_dir,  # Nu en sträng
            QFileDialog.ShowDirsOnly
        )
        
        if directory:
            print(f"Markdown output directory selected: {directory}")
            self.selected_paths['markdown_output'] = directory  # Spara som sträng
            if self.settings_manager:
                self.settings_manager.update_setting('paths', 'select_markdown_output_reverse_dir', directory)
            self.markdown_output_selected.emit(directory)


    # Utility methods
    def get_selected_paths(self) -> dict:
        """Get all currently selected paths"""
        return self.selected_paths.copy()

    def clear_selections(self):
        """Clear all selected paths"""
        self.selected_paths.clear()

    def cleanup(self):
        """Clean up all running threads and resources"""
        print("Cleaning up RadiobuttonFrame resources")
        if hasattr(self, 'markdown_reverse_thread') and self.markdown_reverse_thread is not None:
            if hasattr(self, 'markdown_reverse_worker'):
                self.markdown_reverse_worker.deleteLater()
            self.markdown_reverse_thread.quit()
            self.markdown_reverse_thread.wait()
            self.markdown_reverse_thread.deleteLater()

        if hasattr(self, 'csv_reverse_thread') and self.csv_reverse_thread is not None:
            if hasattr(self, 'csv_reverse_worker'):
                self.csv_reverse_worker.deleteLater()
            self.csv_reverse_thread.quit()
            self.csv_reverse_thread.wait()
            self.csv_reverse_thread.deleteLater()

    def closeEvent(self, event):
        """Ensure proper cleanup on widget closure"""
        self.cleanup()
        super().closeEvent(event)


class ScrollableFrame(QFrame):
    """Scrollable frame with switches"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Scroll Area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Content Widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add switches
        self.switches = []
        for i in range(100):
            switch = QCheckBox(f"Switch {i}")
            switch.setFont(Fonts.get_default(10))
            self.content_layout.addWidget(switch)
            self.switches.append(switch)
            
            if i in (0, 4):  # Select switches 0 and 4
                switch.setChecked(True)
        
        self.scroll_area.setWidget(self.content_widget)
        self.layout.addWidget(self.scroll_area)
        
        # Styling
        self.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {ThemeColors.PRIMARY.value};
            }}
            QCheckBox {{
                color: {ThemeColors.TEXT_PRIMARY.value};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {ThemeColors.TERTIARY.value};
                border-radius: 4px;
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
            }}
            QCheckBox::indicator:checked {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
                border-color: {ThemeColors.PRIMARY_BUTTONS.value};
            }}
            QCheckBox::indicator:hover {{
                border-color: {ThemeColors.HOVER_BUTTONS.value};
            }}
        """)

class CheckboxFrame(QFrame):
    """Frame containing extraction checkboxes"""
    extract_csv_changed = Signal(bool)
    extract_markdown_changed = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # CSV Checkbox
        self.checkbox_extract_csv = QCheckBox("Extract - CSV")
        self.checkbox_extract_csv.setFont(Fonts.get_default(10))
        self.layout.addWidget(self.checkbox_extract_csv)
        
        # Markdown Checkbox
        self.checkbox_extract_markdown = QCheckBox("Extract - Markdown")
        self.checkbox_extract_markdown.setFont(Fonts.get_default(10))
        self.layout.addWidget(self.checkbox_extract_markdown)
        
        # Add stretching space
        self.layout.addStretch()
        
        # Styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.PRIMARY.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 4px;
            }}
            QCheckBox {{
                color: {ThemeColors.TEXT_PRIMARY.value};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {ThemeColors.TERTIARY.value};
                border-radius: 4px;
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
            }}
            QCheckBox::indicator:checked {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
                border-color: {ThemeColors.PRIMARY_BUTTONS.value};
            }}
            QCheckBox::indicator:hover {{
                border-color: {ThemeColors.HOVER_BUTTONS.value};
            }}
        """)

    def setup_connections(self):
        self.checkbox_extract_csv.stateChanged.connect(
            lambda state: self.extract_csv_changed.emit(bool(state))
        )
        self.checkbox_extract_markdown.stateChanged.connect(
            lambda state: self.extract_markdown_changed.emit(bool(state))
        )

    @property
    def extract_csv(self) -> bool:
        return self.checkbox_extract_csv.isChecked()
        
    @property
    def extract_markdown(self) -> bool:
        return self.checkbox_extract_markdown.isChecked()

class EntryRunFrame(QFrame):
    """Frame for handling extractions with improved thread management"""
    run_triggered = Signal()
    extraction_progress = Signal(str, int)  # type, progress value
    extraction_status = Signal(str, str)    # type, status message

    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()
        self.setup_connections()
        
        # Track active extractions
        self.active_extractions = []

        # Set initial directory from settings
        base_dir = self.settings_manager.get_setting("paths", "base_dir", "")
        if base_dir:
            self.entry_path.setText(base_dir)

    def setup_ui(self):
        """Initialize and setup the UI components"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Path entry group
        self.path_group = QFrame()
        path_layout = QHBoxLayout(self.path_group)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(10)

        self.entry_path = QLineEdit()
        self.entry_path.setPlaceholderText("Click to select directory...")
        self.entry_path.setFont(Fonts.get_default(10))
        self.entry_path.setReadOnly(True)
        self.entry_path.setCursor(Qt.PointingHandCursor)
        path_layout.addWidget(self.entry_path)

        self.layout.addWidget(self.path_group)

        # Run button with status indicator
        self.run_button = QPushButton("Run")
        self.run_button.setFont(Fonts.get_bold(10))
        self.run_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout.addWidget(self.run_button)

        # Progress section
        self.progress_frame = QFrame()
        self.progress_layout = QVBoxLayout(self.progress_frame)
        self.progress_layout.setContentsMargins(5, 5, 5, 5)
        self.progress_layout.setSpacing(5)

        # CSV Progress
        self.csv_group = QFrame()
        csv_layout = QVBoxLayout(self.csv_group)
        csv_layout.setContentsMargins(0, 0, 0, 0)
        csv_layout.setSpacing(2)

        self.csv_progress_label = QLabel("CSV Progress:")
        self.csv_progress_label.setFont(Fonts.get_default(9))
        self.csv_progress = QProgressBar()
        self.csv_progress.setTextVisible(True)
        self.csv_status = QLabel("")
        self.csv_status.setFont(Fonts.get_default(8))
        
        csv_layout.addWidget(self.csv_progress_label)
        csv_layout.addWidget(self.csv_progress)
        csv_layout.addWidget(self.csv_status)
        
        self.progress_layout.addWidget(self.csv_group)

        # Markdown Progress
        self.markdown_group = QFrame()
        markdown_layout = QVBoxLayout(self.markdown_group)
        markdown_layout.setContentsMargins(0, 0, 0, 0)
        markdown_layout.setSpacing(2)

        self.markdown_progress_label = QLabel("Markdown Progress:")
        self.markdown_progress_label.setFont(Fonts.get_default(9))
        self.markdown_progress = QProgressBar()
        self.markdown_progress.setTextVisible(True)
        self.markdown_status = QLabel("")
        self.markdown_status.setFont(Fonts.get_default(8))
        
        markdown_layout.addWidget(self.markdown_progress_label)
        markdown_layout.addWidget(self.markdown_progress)
        markdown_layout.addWidget(self.markdown_status)
        
        self.progress_layout.addWidget(self.markdown_group)

        self.layout.addWidget(self.progress_frame)

        # Initially hide progress sections
        self.csv_group.hide()
        self.markdown_group.hide()

        # Apply styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.PRIMARY.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 4px;
            }}
            QLineEdit {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                padding: 8px;
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 4px;
                margin: 1px;
            }}
            QLineEdit:hover {{
                border-color: {ThemeColors.HOVER_BUTTONS.value};
            }}
            QPushButton {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.HOVER_BUTTONS.value};
            }}
            QPushButton:pressed {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
            }}
            QPushButton:disabled {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                color: #666666;
            }}
            QProgressBar {{
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 2px;
                text-align: center;
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
            }}
            QProgressBar::chunk {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
                width: 1px;
            }}
            QLabel {{
                color: {ThemeColors.TEXT_PRIMARY.value};
            }}
        """)

    def setup_connections(self):
        """Setup signal connections with improved error handling"""
        try:
            # Connect file dialog
            self.entry_path.mousePressEvent = self.open_file_dialog
            
            # Connect run button with state handling
            self.run_button.clicked.connect(self.run_command)

        except Exception as e:
            print(f"Error setting up EntryRunFrame connections: {str(e)}")

    def open_file_dialog(self, event):
        """Handle file dialog for directory selection"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            self.entry_path.text() or ""
        )
        if directory:
            self.entry_path.setText(directory)
            self.settings_manager.update_setting('paths', 'base_dir', directory)
            output_dir = os.path.join(directory, 'output')
            self.settings_manager.update_setting('paths', 'output_dir', output_dir)

    def update_progress(self, extraction_type: str, value: int):
        """Update progress bar for specific extraction type"""
        if extraction_type == "CSV":
            self.csv_progress.setValue(value)
        else:
            self.markdown_progress.setValue(value)

    def update_status(self, extraction_type: str, message: str):
        """Update status label for specific extraction type"""
        if extraction_type == "CSV":
            self.csv_status.setText(message)
        else:
            self.markdown_status.setText(message)

    def handle_extraction_error(self, error_message: str):
        """Handle extraction errors"""
        QMessageBox.critical(
            self,
            "Extraction Error",
            f"An error occurred during extraction:\n{error_message}"
        )
        # Re-enable run button
        self.run_button.setEnabled(True)

    def handle_extraction_finished(self, extraction_type: str):
        """Handle completion of a specific extraction"""
        if extraction_type in self.active_extractions:
            self.active_extractions.remove(extraction_type)
            
            # Hide progress group
            if extraction_type == "CSV":
                self.csv_group.hide()
            else:
                self.markdown_group.hide()
        
        # If all extractions are done
        if not self.active_extractions:
            self.run_button.setEnabled(True)
            QMessageBox.information(
                self,
                "Extraction Complete",
                "All selected extractions completed successfully."
            )
            self.run_triggered.emit()

    def run_command(self):
        """Execute the extraction process with improved thread handling"""
        from extractorz import CSVEx, MarkdownEx

        if not self.entry_path.text():
            QMessageBox.warning(self, "No Directory Selected", "Please select a directory first.")
            return

        selected_path = self.entry_path.text()
        output_path = os.path.join(selected_path, 'output')
        
        try:
            os.makedirs(output_path, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create output directory: {str(e)}")
            return

        main_window = self.window()
        if not hasattr(main_window, 'checkbox_frame'):
            QMessageBox.critical(self, "Error", "Checkbox frame not found.")
            return

        checkbox_frame = main_window.checkbox_frame
        
        # Reset active extractions
        self.active_extractions = []
        
        # Create and start threads for each selected extraction
        if checkbox_frame.extract_markdown:
            try:
                print("Setting up Markdown extraction...")
                
                # Create thread first
                self.markdown_thread = QThread()
                
                # Create worker with class and paths
                self.markdown_worker = ExtractionWorker(
                    MarkdownEx,
                    selected_path,
                    output_path,
                    self.window().settings_path
                )
                print("Created ExtractionWorker instance")
                
                # Move worker to thread
                self.markdown_worker.moveToThread(self.markdown_thread)
                print("Moved worker to thread")
                
                # Connect all signals before starting the thread
                print("Setting up signal connections...")
                
                # Main worker signals
                self.markdown_thread.started.connect(
                    self.markdown_worker.run,
                    Qt.QueuedConnection
                )
                
                self.markdown_worker.progress.connect(
                    lambda v: self.update_progress("Markdown", v),
                    Qt.QueuedConnection
                )
                self.markdown_worker.status.connect(
                    lambda s: self.update_status("Markdown", s),
                    Qt.QueuedConnection
                )
                self.markdown_worker.error.connect(
                    self.handle_extraction_error,
                    Qt.QueuedConnection
                )
                self.markdown_worker.finished.connect(
                    lambda: self.handle_extraction_finished("Markdown"),
                    Qt.QueuedConnection
                )
                
                # Cleanup connections
                self.markdown_worker.finished.connect(
                    self.markdown_thread.quit,
                    Qt.QueuedConnection
                )
                self.markdown_worker.finished.connect(
                    self.markdown_worker.deleteLater,
                    Qt.QueuedConnection
                )
                self.markdown_thread.finished.connect(
                    self.markdown_thread.deleteLater,
                    Qt.QueuedConnection
                )
                
                print("All signals connected")
                
                # Show progress UI
                self.markdown_group.show()
                self.markdown_progress.setValue(0)
                self.markdown_status.setText("Starting extraction...")
                
                # Add to active extractions
                self.active_extractions.append("Markdown")
                
                # Start thread
                print("Starting Markdown thread...")
                self.markdown_thread.start()
                print("Markdown thread started")
                
            except Exception as e:
                print(f"Error in Markdown extraction setup: {str(e)}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Setup Error", 
                                f"Failed to setup Markdown extraction:\n{str(e)}")

        # Similar setup for CSV extraction
        if checkbox_frame.extract_csv:
            try:
                print("Setting up CSV extraction...")
                
                # Create thread first
                self.csv_thread = QThread()
                
                # Create worker with class and paths
                self.csv_worker = ExtractionWorker(
                    CSVEx,
                    selected_path,
                    output_path,
                    self.window().settings_path
                )
                print("Created ExtractionWorker instance")
                
                # Move worker to thread
                self.csv_worker.moveToThread(self.csv_thread)
                print("Moved worker to thread")
                
                # Connect all signals before starting the thread
                print("Setting up signal connections...")
                
                # Main worker signals
                self.csv_thread.started.connect(
                    self.csv_worker.run,
                    Qt.QueuedConnection
                )
                
                self.csv_worker.progress.connect(
                    lambda v: self.update_progress("CSV", v),
                    Qt.QueuedConnection
                )
                self.csv_worker.status.connect(
                    lambda s: self.update_status("CSV", s),
                    Qt.QueuedConnection
                )
                self.csv_worker.error.connect(
                    self.handle_extraction_error,
                    Qt.QueuedConnection
                )
                self.csv_worker.finished.connect(
                    lambda: self.handle_extraction_finished("CSV"),
                    Qt.QueuedConnection
                )
                
                # Cleanup connections
                self.csv_worker.finished.connect(
                    self.csv_thread.quit,
                    Qt.QueuedConnection
                )
                self.csv_worker.finished.connect(
                    self.csv_worker.deleteLater,
                    Qt.QueuedConnection
                )
                self.csv_thread.finished.connect(
                    self.csv_thread.deleteLater,
                    Qt.QueuedConnection
                )
                
                print("All signals connected")
                
                # Show progress UI
                self.csv_group.show()
                self.csv_progress.setValue(0)
                self.csv_status.setText("Starting extraction...")
                
                # Add to active extractions
                self.active_extractions.append("CSV")
                
                # Start thread
                print("Starting CSV thread...")
                self.csv_thread.start()
                print("CSV thread started")
                
            except Exception as e:
                print(f"Error in CSV extraction setup: {str(e)}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Setup Error",
                                f"Failed to setup CSV extraction:\n{str(e)}")

        if not self.active_extractions:
            QMessageBox.information(self, "No Extraction Selected", 
                                "Please select at least one extraction option.")
            return

        # Disable run button while extracting
        self.run_button.setEnabled(False)





    def cleanup(self):
        """Clean up all running threads and resources"""
        if hasattr(self, 'markdown_thread') and self.markdown_thread is not None:
            if hasattr(self, 'markdown_worker'):
                self.markdown_worker.deleteLater()
            self.markdown_thread.quit()
            self.markdown_thread.wait()
            self.markdown_thread.deleteLater()

        if hasattr(self, 'csv_thread') and self.csv_thread is not None:
            if hasattr(self, 'csv_worker'):
                self.csv_worker.deleteLater()
            self.csv_thread.quit()
            self.csv_thread.wait()
            self.csv_thread.deleteLater()

    def closeEvent(self, event):
        """Handle widget closure"""
        self.cleanup()
        super().closeEvent(event)


class QuickPasteFrame(QFrame):
    """Frame for quick paste-to-file functionality"""
    
    extraction_started = Signal()
    extraction_finished = Signal()
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()
        self.setup_connections()
        
        # Get output directory from settings
        self.output_dir = self.settings_manager.get_setting(
            'paths', 'select_markdown_output_reverse_dir', ''
        )
        if isinstance(self.output_dir, list):
            self.output_dir = self.output_dir[0] if self.output_dir else ''

    def setup_ui(self):
        """Initialize and setup the UI components"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Header
        self.header = QLabel("Quick Paste Extraction")
        self.header.setFont(Fonts.get_bold(12))
        self.layout.addWidget(self.header)

        # Text area for pasting
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Paste your code snippets here...")
        self.text_edit.setMinimumHeight(200)
        # Install event filter for key press handling
        self.text_edit.installEventFilter(self)
        self.layout.addWidget(self.text_edit)

        # Button row
        self.button_layout = QHBoxLayout()
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setFont(Fonts.get_default(10))
        
        # Extract button
        self.extract_button = QPushButton("Extract Files")
        self.extract_button.setFont(Fonts.get_bold(10))
        
        self.button_layout.addWidget(self.clear_button)
        self.button_layout.addWidget(self.extract_button)
        self.layout.addLayout(self.button_layout)

        # Progress section
        self.progress_frame = QFrame()
        progress_layout = QVBoxLayout(self.progress_frame)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(5)

        self.progress_label = QLabel("Progress:")
        self.progress_label.setFont(Fonts.get_default(9))
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("")
        self.status_label.setFont(Fonts.get_default(8))

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)

        self.layout.addWidget(self.progress_frame)
        self.progress_frame.hide()

        # Apply styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.PRIMARY.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 4px;
            }}
            QLabel {{
                color: {ThemeColors.TEXT_PRIMARY.value};
            }}
            QTextEdit {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 4px;
                padding: 8px;
            }}
            QPushButton {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.HOVER_BUTTONS.value};
            }}
            QProgressBar {{
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 2px;
                text-align: center;
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
            }}
            QProgressBar::chunk {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
            }}
        """)

    def setup_connections(self):
        """Setup signal connections"""
        self.clear_button.clicked.connect(self.clear_text)
        self.extract_button.clicked.connect(self.extract_files)

    def clear_text(self):
        """Clear the text edit area"""
        self.text_edit.clear()

    def eventFilter(self, obj, event):
        """Handle key events for the text edit"""
        if obj == self.text_edit and event.type() == QEvent.Type.KeyPress:
            key_event = QKeyEvent(event)
            if key_event.key() == Qt.Key.Key_Return or key_event.key() == Qt.Key.Key_Enter:
                if key_event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    # Shift+Enter: Insert new line
                    cursor = self.text_edit.textCursor()
                    cursor.insertText('\n')
                else:
                    # Enter without shift: Start extraction
                    self.extract_files()
                return True
        return super().eventFilter(obj, event)

    def extract_files(self):
        """Extract files from pasted content"""
        content = self.text_edit.toPlainText()
        if not content.strip():
            QMessageBox.warning(self, "No Content", "Please paste some content first.")
            return

        if not self.output_dir:
            QMessageBox.warning(self, "No Output Directory", 
                              "Output directory not set in settings.")
            return

        # Create temporary markdown file
        temp_dir = os.path.join(self.output_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_file = os.path.join(temp_dir, 'temp_markdown.md')

        try:
            # Save content to temporary file
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)

            # Show progress UI
            self.progress_frame.show()
            self.extract_button.setEnabled(False)
            self.extraction_started.emit()

            # Create extractor instance
            extractor = ReverseMarkdownEx(temp_file, self.output_dir)
            extractor.update_progress = self.update_progress
            extractor.update_status = self.update_status

            # Create worker and thread
            self.thread = QThread()
            self.worker = ExtractionWorker(extractor)
            self.worker.moveToThread(self.thread)

            # Connect signals
            self.worker.finished.connect(self.on_extraction_finished)
            self.worker.error.connect(self.on_extraction_error)
            self.thread.started.connect(self.worker.run)

            # Start extraction
            self.thread.start()

        except Exception as e:
            self.on_extraction_error(str(e))

    def update_progress(self, value: int):
        """Update progress bar"""
        self.progress_bar.setValue(value)

    def update_status(self, message: str):
        """Update status label"""
        self.status_label.setText(message)

    def on_extraction_finished(self):
        """Handle extraction completion"""
        self.thread.quit()
        self.thread.wait()
        
        # Cleanup temporary files
        temp_dir = os.path.join(self.output_dir, 'temp')
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Error cleaning up temp directory: {e}")

        self.extract_button.setEnabled(True)
        self.progress_frame.hide()
        self.extraction_finished.emit()
        
        # Clear the text edit after successful extraction
        self.text_edit.clear()
        
        QMessageBox.information(
            self,
            "Extraction Complete",
            f"Files have been extracted to:\n{self.output_dir}"
        )

    def on_extraction_error(self, error_message: str):
        """Handle extraction errors"""
        self.extract_button.setEnabled(True)
        self.progress_frame.hide()
        
        QMessageBox.critical(
            self,
            "Extraction Error",
            f"An error occurred during extraction:\n{error_message}"
        )

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings_path = "./settings.toml"
        self.resource_manager = ResourceManager()
        self.settings_manager = SettingsManager(self.settings_path)
        self.resource_manager.register_resource('settings_manager', self.settings_manager, 
                                             lambda x: x._save_settings())
        
        self.ui_components = {}
        self.setWindowTitle("Project Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create status bar for progress updates
        self.statusBar()
        
        # Initialize central widget with delayed UI loading
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QGridLayout(self.central_widget)
        
        # Delayed UI initialization
        QTimer.singleShot(0, self.setup_ui)
        QTimer.singleShot(100, self.setup_connections)
        QTimer.singleShot(200, lambda: AppTheme.apply_theme(QApplication.instance()))

    def setup_ui(self):
        """Initialize UI with lazy loading and caching"""
        # Cache layout settings
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Initialize components with visibility optimization
        self.ui_components['sidebar'] = self.create_sidebar()
        self.ui_components['textbox'] = self.create_scrollable_textbox()
        self.ui_components['tabview'] = self.create_tabview()
        self.ui_components['right_panel'] = self.create_right_panel()
        self.ui_components['checkbox'] = self.create_checkbox()
        self.ui_components['entry_run'] = self.create_entry_run()
        
        # Layout components
        self.layout_components()
        
        # Configure stretching
        self.configure_layout_stretch()

    def create_sidebar(self):
        sidebar = SidebarFrame(self)
        sidebar.setAttribute(Qt.WA_WState_Hidden, True)
        self.main_layout.addWidget(sidebar, 0, 0, 4, 1)
        return sidebar

    def create_scrollable_textbox(self):
        textbox = ScrollableTextboxFrame(self.settings_manager, self)
        self.main_layout.addWidget(textbox, 0, 1, 1, 2)
        return textbox

    def create_tabview(self):
        tabview = TabViewFrame(self.settings_manager, self)
        self.main_layout.addWidget(tabview, 0, 3, 2, 1)
        return tabview

    def create_right_panel(self):
        right_panel = QTabWidget()
        self.style_tab_widget(right_panel)
        
        # Lazy load tab contents
        radiobutton = RadiobuttonFrame(settings_manager=self.settings_manager, parent=self)
        quickpaste = QuickPasteFrame(self.settings_manager, self)
        
        right_panel.addTab(radiobutton, "Standard Extraction")
        right_panel.addTab(quickpaste, "Quick Paste")
        
        self.main_layout.addWidget(right_panel, 0, 4, 2, 1)
        return right_panel

    def create_checkbox(self):
        checkbox = CheckboxFrame(self)
        self.main_layout.addWidget(checkbox, 2, 4, 1, 1)
        self.checkbox_frame = checkbox  # Add this line
        return checkbox

    def create_entry_run(self):
        entry_run = EntryRunFrame(self.settings_manager, self)
        self.main_layout.addWidget(entry_run, 3, 1, 1, 4)
        return entry_run

    def layout_components(self):
        """Configure layout with cached components"""
        for component in self.ui_components.values():
            if hasattr(component, 'show'):
                component.show()

    def configure_layout_stretch(self):
        """Configure layout stretching factors"""
        column_stretches = {0: 1, 1: 2, 2: 1, 3: 1, 4: 1, 5: 1}
        row_stretches = {0: 2, 1: 1, 2: 1, 3: 1}
        
        for col, stretch in column_stretches.items():
            self.main_layout.setColumnStretch(col, stretch)
        for row, stretch in row_stretches.items():
            self.main_layout.setRowStretch(row, stretch)

    def setup_connections(self):
        """Setup optimized signal connections"""
        try:
            self.connect_signals()
        except Exception as e:
            self.handle_connection_error(e)

    def connect_signals(self):
        """Connect all signals with proper error handling"""
        connections = {
            'setting_changed': (
                self.ui_components['textbox'].setting_changed,
                self.handle_setting_change
            ),
            'preset_changed': (
                self.ui_components['tabview'].preset_changed,
                self.handle_preset_change
            ),
            'appearance_changed': (
                self.ui_components['sidebar'].appearance_mode_changed,
                self.handle_appearance_change
            ),
            'extraction_started': (
                self.ui_components['right_panel'].widget(1).extraction_started,
                lambda: self.handle_extraction_state("started")
            ),
            'extraction_finished': (
                self.ui_components['right_panel'].widget(1).extraction_finished,
                lambda: self.handle_extraction_state("finished")
            ),
            'csv_changed': (
                self.ui_components['checkbox'].extract_csv_changed,
                lambda state: self.handle_extraction_option_change('csv', state)
            ),
            'markdown_changed': (
                self.ui_components['checkbox'].extract_markdown_changed,
                lambda state: self.handle_extraction_option_change('markdown', state)
            ),
            'run_triggered': (
                self.ui_components['entry_run'].run_triggered,
                self.handle_run_command
            )
        }
        
        for name, (signal, slot) in connections.items():
            try:
                signal.connect(slot)
            except Exception as e:
                print(f"Error connecting {name}: {e}")

    @staticmethod
    def style_tab_widget(widget):
        """Apply cached styling to tab widget"""
        widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 4px;
                background-color: {ThemeColors.PRIMARY.value};
            }}
            QTabBar::tab {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                padding: 8px 16px;
                margin: 2px;
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
            }}
            QTabBar::tab:hover {{
                background-color: {ThemeColors.HOVER_BUTTONS.value};
            }}
        """)

    def handle_connection_error(self, error):
        """Centralized error handling for connections"""
        print(f"Error setting up connections: {error}")
        QMessageBox.critical(
            self,
            "Connection Error",
            f"An error occurred while setting up connections:\n{str(error)}"
        )

    def handle_extraction_state(self, state: str):
        """Optimized state handling with batch updates"""
        try:
            widgets_state = state == "finished"
            
            # Batch update UI state
            for widget in (self.ui_components['right_panel'], 
                         self.ui_components['entry_run'],
                         self.ui_components['checkbox']):
                widget.setEnabled(widgets_state)
            
            # Update status bar
            if hasattr(self, 'statusBar'):
                message = "Extraction completed" if widgets_state else "Extraction in progress..."
                self.statusBar().showMessage(message, 3000 if widgets_state else 0)
            
        except Exception as e:
            self.handle_state_error(e)

    def handle_state_error(self, error):
        """Handle state change errors"""
        print(f"Error handling state: {error}")
        QMessageBox.warning(
            self,
            "State Change Error",
            f"An error occurred while updating the application state:\n{str(error)}"
        )

    def handle_setting_change(self, section: str, key: str, value: str):
        """Handle settings changes with caching"""
        print(f"Setting changed - {section}.{key}: {value}")
        if section in self.ui_components:
            self.ui_components[section].update()

    def handle_preset_change(self, preset_name: str, files: list):
        print(f"Preset '{preset_name}' changed - {len(files)} files")
        if 'tabview' in self.ui_components:
            self.ui_components['tabview'].load_preset_files(preset_name)

    def handle_appearance_change(self, mode: str):
        """Handle theme changes with caching"""
        AppTheme.apply_theme(QApplication.instance())

    def handle_extraction_option_change(self, extraction_type: str, enabled: bool):
        """Handle extraction option changes"""
        print(f"{extraction_type} extraction {'enabled' if enabled else 'disabled'}")
        if 'entry_run' in self.ui_components:
            component = self.ui_components['entry_run']
            if hasattr(component, f'{extraction_type}_group'):
                getattr(component, f'{extraction_type}_group').setVisible(enabled)

    def handle_run_command(self):
        """Handle run command with state management"""
        if not self.ui_components['entry_run'].isEnabled():
            return
        print("Run command triggered")
        self.handle_extraction_state("started")

    def closeEvent(self, event):
        """Handle application closure with proper cleanup"""
        self.resource_manager.cleanup()
        for component in self.ui_components.values():
            if hasattr(component, 'cleanup'):
                component.cleanup()
        event.accept()

if __name__ == "__main__":
    app = QApplication([])
    window = App()
    window.show()
    app.exec()
