# ./frontend/pages/qframes/settings/settings_frame.py

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import toml
import os
from enum import Enum
from PySide6.QtGui import QColor, QPalette, QFont, QKeyEvent
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QLineEdit, QListWidget, QMessageBox, QInputDialog,
    QFileDialog, QComboBox
)


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
    """Manages application settings with signals for PySide6"""
    
    settings_changed = Signal()
    
    def __init__(self, settings_path: str):
        super().__init__()
        self._settings_path = Path(settings_path).resolve()
        self._settings: Optional[SettingsData] = None
        self._load_settings()

    def _create_default_settings(self) -> SettingsData:
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
        try:
            if not self._settings_path.exists():
                self._settings = self._create_default_settings()
                self._save_settings()
                return

            with self._settings_path.open('r', encoding='utf-8') as f:
                content = f.read().replace('\\', '/')
                data = toml.loads(content)
                
            self._settings = SettingsData(**data)
            self._normalize_paths()
            
        except Exception as e:
            print(f"Error loading settings: {e}")
            self._settings = self._create_default_settings()
            self._save_settings()

    def _normalize_paths(self) -> None:
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

    def _save_settings(self) -> None:
        if not self._settings:
            return
            
        try:
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            settings_dict = {
                field: getattr(self._settings, field)
                for field in self._settings.__annotations__
            }
            
            with self._settings_path.open('w', encoding='utf-8') as f:
                toml.dump(settings_dict, f)
                
        except Exception as e:
            print(f"Error saving settings: {e}")

    def update_setting(self, section: str, key: str, value: Any) -> None:
        if not self._settings:
            return

        section_dict = getattr(self._settings, section, None)
        if section_dict is None:
            section_dict = {}
            setattr(self._settings, section, section_dict)

        if isinstance(section_dict, dict):
            if key not in section_dict:
                section_dict[key] = value if isinstance(value, list) else [value]
            elif isinstance(section_dict[key], list) and isinstance(value, list):
                section_dict[key].extend(v for v in value if v not in section_dict[key])
            else:
                section_dict[key] = value

            self._save_settings()
            self.settings_changed.emit()

    def get_setting(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        if not self._settings or not hasattr(self._settings, section):
            return default

        section_dict = getattr(self._settings, section)
        if key is None:
            return section_dict
        return section_dict.get(key, default)
    
    def get_section(self, section: str, default: Any = None) -> Any:
        if not self._settings or not hasattr(self._settings, section):
            return default
        return getattr(self._settings, section)
    
    def remove_setting(self, section: str, key: str) -> None:
        if not self._settings or not hasattr(self._settings, section):
            return

        section_dict = getattr(self._settings, section)
        if isinstance(section_dict, dict) and key in section_dict:
            del section_dict[key]
            self._save_settings()
            self.settings_changed.emit()

class SettingsFrame(QFrame):
    """Frame for managing application settings and presets"""
    
    setting_changed = Signal(str, str, str)  # section, key, value
    preset_changed = Signal(str, list)       # preset_name, files
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()
        self.setup_connections()
        self.load_settings()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)

        # File Specific Settings
        self.use_file_specific_combo = QComboBox()
        self.use_file_specific_combo.addItems(["True", "False"])
        self.layout.addWidget(QLabel("Enable File Specific:"))
        self.layout.addWidget(self.use_file_specific_combo)

        # File List
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.layout.addWidget(QLabel("Files:"))
        self.layout.addWidget(self.file_list)

        # Buttons
        button_layout = QHBoxLayout()
        self.add_file_button = QPushButton("Add File")
        self.add_folder_button = QPushButton("Add Folder")
        button_layout.addWidget(self.add_file_button)
        button_layout.addWidget(self.add_folder_button)
        self.layout.addLayout(button_layout)

        # Presets
        self.preset_combo = QComboBox()
        self.layout.addWidget(QLabel("Presets:"))
        self.layout.addWidget(self.preset_combo)

        preset_button_layout = QHBoxLayout()
        self.add_preset_button = QPushButton("Add Preset")
        self.remove_preset_button = QPushButton("Remove Preset")
        preset_button_layout.addWidget(self.add_preset_button)
        preset_button_layout.addWidget(self.remove_preset_button)
        self.layout.addLayout(preset_button_layout)

    def setup_connections(self):
        # File Specific Toggle
        self.use_file_specific_combo.currentTextChanged.connect(self.handle_file_specific_change)

        # File Management
        self.add_file_button.clicked.connect(self.add_files)
        self.add_folder_button.clicked.connect(self.add_folder)
        self.file_list.itemSelectionChanged.connect(self.handle_file_selection)

        # Preset Management
        self.preset_combo.currentTextChanged.connect(self.load_preset)
        self.add_preset_button.clicked.connect(self.add_preset)
        self.remove_preset_button.clicked.connect(self.remove_preset)

    def load_settings(self):
        # Load File Specific Setting
        use_file_specific = self.settings_manager.get_setting(
            "file_specific", 
            "use_file_specific", 
            False
        )
        self.use_file_specific_combo.setCurrentText(str(use_file_specific))

        # Load Presets
        presets = self.settings_manager.get_section("presets", {})
        self.preset_combo.clear()
        self.preset_combo.addItems(presets.keys())

    def handle_file_specific_change(self, value: str):
        self.settings_manager.update_setting(
            'file_specific', 
            'use_file_specific', 
            value == "True"
        )
        self.setting_changed.emit('file_specific', 'use_file_specific', value)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            self.settings_manager.get_setting("paths", "base_dir", "")
        )
        
        if files:
            self._add_files_to_preset(files)

    def add_folder(self):
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
        self.load_preset(preset_name)
        self.preset_changed.emit(preset_name, preset_files)

    def load_preset(self, preset_name: str):
        if not preset_name:
            return
        
        self.file_list.clear()
        preset_files = self.settings_manager.get_setting("presets", preset_name, [])
        self.file_list.addItems(preset_files)

    def add_preset(self):
        name, ok = QInputDialog.getText(
            self,
            "Preset Name",
            "Enter the name for the new preset:"
        )
        if ok and name:
            self.settings_manager.update_setting("presets", name, [])
            self.preset_combo.addItem(name)
            self.preset_combo.setCurrentText(name)
            self.load_preset(name)

    def remove_preset(self):
        preset_name = self.preset_combo.currentText()
        if not preset_name:
            return

        confirmation = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove the preset '{preset_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirmation == QMessageBox.Yes:
            self.settings_manager.remove_setting("presets", preset_name)
            self.preset_combo.removeItem(self.preset_combo.findText(preset_name))
            self.file_list.clear()
            self.preset_changed.emit(preset_name, [])

    def handle_file_selection(self):
        """Handle changes in file selection"""
        selected_items = self.file_list.selectedItems()
        # Enable/disable relevant buttons based on selection
        self.remove_preset_button.setEnabled(bool(selected_items))


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

