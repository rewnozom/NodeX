import os
from typing import Dict, Any

from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QPushButton, QLabel, QScrollArea, QWidget, QLineEdit, QGridLayout, QFileDialog, QHBoxLayout
)
from Config.AppConfig.settings_manager import SettingsManager
from Config.AppConfig.SettingWidgetGroup import SettingWidgetGroup
from frontend.Theme.fonts import Fonts
from Utils.Enums.enums import ThemeColors


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
