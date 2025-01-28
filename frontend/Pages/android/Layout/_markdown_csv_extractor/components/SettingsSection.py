# ./_markdown_csv_extractor/components/SettingsSection.py

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, QPushButton, QListWidget, QMessageBox
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
from ..GUI_Constants_and_Settings import GuiConstants
from ..GUI_Constants_and_Settings import SettingsManager  # Ensure correct import
import sys

class SettingsSection(QFrame):
    """Combined Settings section for Paths, Files, and Directories"""
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Paths Subsection
        paths_label = QLabel("[Paths]")
        paths_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(paths_label)

        # Base Directory
        base_dir_layout = QHBoxLayout()
        self.base_dir_input = QLineEdit(self.settings_manager.get_setting("paths", "base_dir", ""))
        self.base_dir_input.setReadOnly(True)
        self.base_dir_input.setPlaceholderText("Select Base Directory")
        base_dir_button = QPushButton("Browse")
        base_dir_button.clicked.connect(lambda: self.choose_directory("base_dir"))
        base_dir_layout.addWidget(self.base_dir_input)
        base_dir_layout.addWidget(base_dir_button)
        layout.addLayout(base_dir_layout)

        # Output Directory
        output_dir_layout = QHBoxLayout()
        self.output_dir_input = QLineEdit(self.settings_manager.get_setting("paths", "output_dir", ""))
        self.output_dir_input.setReadOnly(True)
        self.output_dir_input.setPlaceholderText("Select Output Directory")
        output_dir_button = QPushButton("Browse")
        output_dir_button.clicked.connect(lambda: self.choose_directory("output_dir"))
        output_dir_layout.addWidget(self.output_dir_input)
        output_dir_layout.addWidget(output_dir_button)
        layout.addLayout(output_dir_layout)

        # Files Subsection
        files_label = QLabel("[Files]")
        files_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(files_label)

        # Ignored Extensions
        ignored_ext_layout = QHBoxLayout()
        self.ignored_extensions_input = QLineEdit(
            ", ".join(self.settings_manager.get_setting("files", "ignored_extensions", []))
        )
        self.ignored_extensions_input.setPlaceholderText("e.g., .exe, .dll")
        self.ignored_extensions_input.textChanged.connect(self.update_ignored_extensions)
        ignored_ext_layout.addWidget(QLabel("Ignored Extensions:"))
        ignored_ext_layout.addWidget(self.ignored_extensions_input)
        layout.addLayout(ignored_ext_layout)

        # Ignored Files
        ignored_files_label = QLabel("Ignored Files:")
        self.ignored_files_list = QListWidget()
        specific_files = self.settings_manager.get_setting("files", "ignored_files", [])
        self.ignored_files_list.addItems(specific_files)
        self.ignored_files_list.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(ignored_files_label)
        layout.addWidget(self.ignored_files_list)

        # Add File and Folder Buttons
        add_file_button = QPushButton("Add File")
        add_folder_button = QPushButton("Add Folder")
        add_file_button.clicked.connect(self.add_files)  # Changed to add_files for multiple selection
        add_folder_button.clicked.connect(self.add_folder)
        layout.addWidget(add_file_button)
        layout.addWidget(add_folder_button)

        # Directories Subsection
        directories_label = QLabel("[Directories]")
        directories_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(directories_label)

        # Ignored Directories
        ignored_dirs_label = QLabel("Ignored Directories:")
        self.ignored_dirs_list = QListWidget()
        ignored_dirs = self.settings_manager.get_setting("directories", "ignored_directories", [])
        self.ignored_dirs_list.addItems(ignored_dirs)
        self.ignored_dirs_list.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(ignored_dirs_label)
        layout.addWidget(self.ignored_dirs_list)

    def choose_directory(self, dir_type: str):
        """Open directory dialog and save selection"""
        print(f"SettingsSection: Choosing directory for {dir_type}")  # Debug
        directory = QFileDialog.getExistingDirectory(self, f"Select {dir_type.replace('_', ' ').title()} Directory")
        if directory:
            relative_directory = self.settings_manager.absolute_to_relative(directory)
            self.settings_manager.update_setting("paths", dir_type, relative_directory)
            print(f"SettingsSection: Selected {dir_type}: {relative_directory}")  # Debug
            if dir_type == "base_dir":
                self.base_dir_input.setText(directory)
                # Auto-set output directory
                output_dir = str(Path(directory) / "output")
                relative_output_dir = self.settings_manager.absolute_to_relative(output_dir)
                self.settings_manager.update_setting("paths", "output_dir", relative_output_dir)
                self.output_dir_input.setText(output_dir)
            elif dir_type == "output_dir":
                self.output_dir_input.setText(directory)
        else:
            print(f"SettingsSection: No directory selected for {dir_type}")  # Debug

    def update_ignored_extensions(self):
        """Update ignored extensions in settings"""
        extensions = [ext.strip() for ext in self.ignored_extensions_input.text().split(",") if ext.strip()]
        self.settings_manager.update_setting("files", "ignored_extensions", extensions)
        print(f"SettingsSection: Updated ignored_extensions: {extensions}")  # Debug

    def add_files(self):
        """Add multiple files to the ignored files list"""
        print("SettingsSection: Adding files to ignored_files")  # Debug
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files to Ignore",
            self.settings_manager.relative_to_absolute(self.settings_manager.get_setting("paths", "base_dir", "")),
            "All Files (*.*)"
        )
        if files:
            current_items = [self.ignored_files_list.item(i).text() for i in range(self.ignored_files_list.count())]
            for file_path in files:
                relative_path = self.settings_manager.absolute_to_relative(file_path)
                if relative_path not in current_items:
                    self.ignored_files_list.addItem(relative_path)
                    print(f"SettingsSection: Added ignored file: {relative_path}")  # Debug
            self.update_ignored_files()

    def add_folder(self):
        """Add all files from a folder to the ignored files list"""
        print("SettingsSection: Adding folder to ignored_files")  # Debug
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Ignore",
            self.settings_manager.relative_to_absolute(self.settings_manager.get_setting("paths", "base_dir", ""))
        )
        if folder:
            for root, _, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = self.settings_manager.absolute_to_relative(file_path)
                    if relative_path not in [self.ignored_files_list.item(i).text() for i in range(self.ignored_files_list.count())]:
                        self.ignored_files_list.addItem(relative_path)
                        print(f"SettingsSection: Added ignored file from folder: {relative_path}")  # Debug
            self.update_ignored_files()

    def update_ignored_files(self):
        """Update the ignored files in settings"""
        ignored_files = [self.ignored_files_list.item(i).text() for i in range(self.ignored_files_list.count())]
        self.settings_manager.update_setting("files", "ignored_files", ignored_files)
        print(f"SettingsSection: Updated ignored_files list")  # Debug
