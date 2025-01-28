import os
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QComboBox, QPushButton, QListWidget, QMessageBox, QInputDialog, QFileDialog
)
from Config.AppConfig.settings_manager import SettingsManager
from frontend.Theme.fonts import Fonts
from ui.widgets.custom_list_widget import CustomListWidget
from Utils.Enums.enums import ThemeColors


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
