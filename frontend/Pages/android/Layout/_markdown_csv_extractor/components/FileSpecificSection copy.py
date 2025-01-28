# ./_markdown_csv_extractor/components/FileSpecificSection.py

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QListWidget, QMessageBox, QInputDialog, QComboBox, QFileDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtCore import (
    Qt, Signal, QObject, QTimer, QThread, Slot,
    QPoint, QPropertyAnimation, QEasingCurve
)
from PySide6.QtGui import (
    QFont, QPalette, QColor, QKeyEvent
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea, QLineEdit,
    QFileDialog, QMessageBox, QCheckBox, QProgressBar,
    QListWidget, QSizePolicy, QInputDialog, QComboBox, QSplitter, QScrollerProperties, QScroller
)


import os
from pathlib import Path
from ..Theme import ThemeColors
from ..GUI_Constants_and_Settings import GuiConstants, SettingsManager

class FileSpecificSection(QFrame):
    """Section for handling file-specific settings"""
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header = QLabel("File Specific Settings")
        header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(header)

        # Enable/Disable file specific toggle
        self.file_specific_toggle = QCheckBox("Enable File Specific")
        use_file_specific = self.settings_manager.get_setting("file_specific", "use_file_specific", False)
        self.file_specific_toggle.setChecked(use_file_specific)
        self.file_specific_toggle.toggled.connect(self.toggle_file_specific)
        layout.addWidget(self.file_specific_toggle)

        # File list for specific files
        self.file_list = QListWidget()
        specific_files = self.settings_manager.get_setting("file_specific", "specific_files", [])
        self.file_list.addItems(specific_files)
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.file_list.setFixedHeight(200)  # Adjusted height to show ~6-8 rows
        self.file_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(QLabel("Specific Files"))
        layout.addWidget(self.file_list)

        # Buttons for file management
        add_file_button = QPushButton("Add File")
        add_folder_button = QPushButton("Add Folder")
        remove_file_button = QPushButton("Remove Selected File(s)")
        add_file_button.clicked.connect(self.add_files)
        add_folder_button.clicked.connect(self.add_folder)
        remove_file_button.clicked.connect(self.remove_selected_files)
        layout.addWidget(add_file_button)
        layout.addWidget(add_folder_button)
        layout.addWidget(remove_file_button)

        # Presets management
        layout.addWidget(QLabel("Presets"))
        self.preset_dropdown = QComboBox()
        presets = self.settings_manager.get_section("presets", {})
        self.preset_dropdown.addItems(presets.keys())
        self.preset_dropdown.currentTextChanged.connect(self.load_preset_files)
        layout.addWidget(self.preset_dropdown)

        # Preset Buttons
        add_preset_btn = QPushButton("Add Preset")
        remove_preset_btn = QPushButton("Remove Preset")
        add_preset_btn.clicked.connect(self.add_preset)
        remove_preset_btn.clicked.connect(self.remove_preset)
        layout.addWidget(add_preset_btn)
        layout.addWidget(remove_preset_btn)

        # Preset File Management Buttons
        layout.addWidget(QLabel("Manage Preset Files"))
        add_preset_file_btn = QPushButton("Add File to Preset")
        add_preset_folder_btn = QPushButton("Add Folder to Preset")
        add_preset_file_btn.clicked.connect(self.add_preset_files)
        add_preset_folder_btn.clicked.connect(self.add_preset_folder)
        layout.addWidget(add_preset_file_btn)
        layout.addWidget(add_preset_folder_btn)

    def toggle_file_specific(self, enabled: bool):
        """Toggle file-specific mode"""
        self.settings_manager.update_setting("file_specific", "use_file_specific", enabled)
        print(f"FileSpecificSection: File specific mode {'enabled' if enabled else 'disabled'}")  # Debug

    def add_files(self):
        """Add multiple specific files"""
        print("FileSpecificSection: Adding files to specific_files")  # Debug
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            self.settings_manager.relative_to_absolute(self.settings_manager.get_setting("paths", "base_dir", "")),
            "All Files (*.*)"
        )
        if files:
            current_items = [self.file_list.item(i).text() for i in range(self.file_list.count())]
            for file_path in files:
                relative_path = self.settings_manager.absolute_to_relative(file_path)
                if relative_path not in current_items:
                    self.file_list.addItem(relative_path)
                    print(f"FileSpecificSection: Added specific file: {relative_path}")  # Debug
            self.update_specific_files()

    def add_folder(self):
        """Add all files from a folder to the specific files list"""
        print("FileSpecificSection: Adding folder to specific_files")  # Debug
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
            self.settings_manager.relative_to_absolute(self.settings_manager.get_setting("paths", "base_dir", ""))
        )
        if folder:
            for root, _, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = self.settings_manager.absolute_to_relative(file_path)
                    if relative_path not in [self.file_list.item(i).text() for i in range(self.file_list.count())]:
                        self.file_list.addItem(relative_path)
                        print(f"FileSpecificSection: Added specific file from folder: {relative_path}")  # Debug
            self.update_specific_files()

    def remove_selected_files(self):
        """Remove selected files from the specific files list"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            print("FileSpecificSection: No files selected for removal")  # Debug
            return
        for item in selected_items:
            print(f"FileSpecificSection: Removing specific file: {item.text()}")  # Debug
            self.file_list.takeItem(self.file_list.row(item))
        self.update_specific_files()

    def update_specific_files(self):
        """Update the list of specific files in settings"""
        specific_files = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        self.settings_manager.update_setting("file_specific", "specific_files", specific_files)
        print(f"FileSpecificSection: Updated specific_files list")  # Debug

    def load_preset_files(self, preset_name: str):
        """Load files for selected preset"""
        if not preset_name:
            return
        self.file_list.clear()
        preset_files = self.settings_manager.get_setting("presets", preset_name, [])
        self.file_list.addItems(preset_files)
        print(f"FileSpecificSection: Loaded preset '{preset_name}' with {len(preset_files)} files")  # Debug

    def add_preset(self):
        """Add a new preset"""
        preset_name, ok = QInputDialog.getText(self, "New Preset", "Enter Preset Name:")
        if ok and preset_name:
            presets = self.settings_manager.get_section("presets", {})
            if preset_name in presets:
                QMessageBox.warning(self, "Preset Exists", f"A preset named '{preset_name}' already exists.")
                print(f"FileSpecificSection: Preset '{preset_name}' already exists")  # Debug
                return
            presets[preset_name] = []
            self.settings_manager.update_section("presets", presets)
            self.preset_dropdown.addItem(preset_name)
            QMessageBox.information(self, "Success", f"Preset '{preset_name}' has been created.")
            print(f"FileSpecificSection: Preset '{preset_name}' created")  # Debug

    def remove_preset(self):
        """Remove the selected preset"""
        preset_name = self.preset_dropdown.currentText()
        if preset_name:
            confirmation = QMessageBox.question(
                self,
                "Confirm Removal",
                f"Are you sure you want to remove the preset '{preset_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirmation == QMessageBox.Yes:
                presets = self.settings_manager.get_section("presets", {})
                if preset_name in presets:
                    del presets[preset_name]
                    self.settings_manager.update_section("presets", presets)
                    self.preset_dropdown.removeItem(self.preset_dropdown.findText(preset_name))
                    QMessageBox.information(self, "Success", f"Preset '{preset_name}' has been removed.")
                    print(f"FileSpecificSection: Preset '{preset_name}' removed")  # Debug

    def add_preset_files(self):
        """Add multiple files to the selected preset"""
        preset_name = self.preset_dropdown.currentText()
        if not preset_name:
            QMessageBox.warning(self, "No Preset Selected", "Please select a preset to add files.")
            print("FileSpecificSection: No preset selected for adding files")  # Debug
            return

        print(f"FileSpecificSection: Adding files to preset '{preset_name}'")  # Debug
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files to Add to Preset",
            self.settings_manager.relative_to_absolute(self.settings_manager.get_setting("paths", "base_dir", "")),
            "All Files (*.*)"
        )
        if files:
            presets = self.settings_manager.get_section("presets", {})
            for file_path in files:
                relative_path = self.settings_manager.absolute_to_relative(file_path)
                if relative_path not in presets[preset_name]:
                    presets[preset_name].append(relative_path)
                    print(f"FileSpecificSection: Added file '{relative_path}' to preset '{preset_name}'")  # Debug
            self.settings_manager.update_section("presets", presets)
            self.load_preset_files(preset_name)

    def add_preset_folder(self):
        """Add all files from a folder to the selected preset"""
        preset_name = self.preset_dropdown.currentText()
        if not preset_name:
            QMessageBox.warning(self, "No Preset Selected", "Please select a preset to add folders.")
            print("FileSpecificSection: No preset selected for adding folders")  # Debug
            return

        print(f"FileSpecificSection: Adding folder to preset '{preset_name}'")  # Debug
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Add to Preset",
            self.settings_manager.relative_to_absolute(self.settings_manager.get_setting("paths", "base_dir", ""))
        )
        if folder:
            all_files = []
            for root, _, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = self.settings_manager.absolute_to_relative(file_path)
                    if relative_path not in self.settings_manager.get_setting("presets", preset_name, []):
                        all_files.append(relative_path)
                        print(f"FileSpecificSection: Added file '{relative_path}' to preset '{preset_name}'")  # Debug
            presets = self.settings_manager.get_section("presets", {})
            presets[preset_name].extend(all_files)
            self.settings_manager.update_section("presets", presets)
            self.load_preset_files(preset_name)
