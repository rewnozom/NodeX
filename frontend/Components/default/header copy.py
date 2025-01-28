#!/usr/bin/env python3
# ./frontend/Components/default/header.py

import sys
import os
from typing import Optional, Dict, Tuple
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QWidget, 
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QToolButton,
    QAbstractButton,
    QDialog,
    QVBoxLayout
)
from Config.AppConfig.config import (
    APP_NAME,
    THEME_LIGHT,
    THEME_DARK,
    UI_LAYOUT_MARGINS,
    UI_LAYOUT_SPACING
)
from Config.AppConfig.icon_config import ICONS
from Styles.theme_manager import ThemeManager
from log.logger import logger
from modules.fast_whisper_v2.main import WhisperHub, WhisperTranscription



class PopupDialog(QDialog):
    """Base class for popup dialogs."""
    def __init__(self, parent=None, title="Popup", width=600, height=400):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setModal(False)
        self.setWindowTitle(title)
        self.setFixedSize(width, height)
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
    def center_relative_to_parent(self):
        if self.parent():
            parent_geometry = self.parent().geometry()
            self.move(parent_geometry.center() - self.rect().center())


class WhisperDialog(PopupDialog):
    def __init__(self, parent=None):
        super().__init__(parent, "Whisper Transcription", 600, 400)
        self.whisper_widget = WhisperHub().whisper_tab
        self.layout.addWidget(self.whisper_widget)

class ProfileDialog(PopupDialog):
    def __init__(self, parent=None):
        super().__init__(parent, "Profile", 400, 300)
        # Add profile content here
        self.layout.addWidget(QLabel("Profile Content"))

class SettingsDialog(PopupDialog):
    def __init__(self, parent=None):
        super().__init__(parent, "Settings", 500, 350)
        # Add settings content here
        self.layout.addWidget(QLabel("Settings Content"))

class TerminalDialog(PopupDialog):
    def __init__(self, parent=None):
        super().__init__(parent, "Terminal", 600, 400)
        # Add terminal content here
        self.layout.addWidget(QLabel("Terminal Content"))
        

class HeaderSection(QWidget):
    """
    Header section component that adapts to both desktop and phone layouts.
    Provides navigation buttons and theme switching functionality.
    """

    PHONE_BUTTON_SIZE = 32
    DESKTOP_BUTTON_SIZE = 24
    PHONE_FONT_SIZE = "14px"
    
    def __init__(self, parent: QWidget):
        """Initialize the header section."""
        super().__init__(parent)
        self.parent = parent
        self._initialize_properties()
        self._setup_ui()
        self._apply_initial_theme()

    def _initialize_properties(self) -> None:
        """Initialize basic properties."""
        self.is_phone_layout = self.parent.config.get('enable_phone_layout', False)
        self.button_size = self.PHONE_BUTTON_SIZE if self.is_phone_layout else self.DESKTOP_BUTTON_SIZE
        self._verify_configuration()

    def _verify_configuration(self) -> None:
        """Verify required configuration exists."""
        required_configs = ['theme', 'enable_phone_layout']
        for config in required_configs:
            if config not in self.parent.config:
                raise ConfigurationError(f"Missing required configuration: {config}")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self._init_layout()
        self._setup_title()
        self._add_spacer()
        self._init_buttons()
        self.set_object_names()

    def _init_layout(self) -> None:
        """Initialize the layout."""
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(*UI_LAYOUT_MARGINS)
        self.layout.setSpacing(UI_LAYOUT_SPACING)

    def _setup_title(self) -> None:
        """Set up the title label."""
        self.title = QLabel(APP_NAME)
        if self.is_phone_layout:
            self.title.setStyleSheet(f"font-size: {self.PHONE_FONT_SIZE};")
        self.layout.addWidget(self.title)

    def _add_spacer(self) -> None:
        """Add spacing to push buttons to the right."""
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.layout.addItem(spacer)

    def _init_buttons(self) -> None:
        """Initialize header buttons based on layout mode."""
        self.buttons = self._create_buttons()
        self._setup_button_connections()

    def _create_buttons(self) -> Dict[str, QAbstractButton]:
        """Create all header buttons."""
        button_configs = {
            'profile': ('user', "Profile"),
            'settings': ('settings', "Settings"),
            'theme': ('moon', "Toggle Theme"),
            'terminal': ('terminal', "Open Terminal"),
            'phone': ('phone', "Open Whisper")
        }

        buttons = {}
        for name, (icon_key, tooltip) in button_configs.items():
            button = (
                self._create_tool_button(icon_key, tooltip, self.button_size)
                if self.is_phone_layout
                else self._create_button(icon_key, tooltip)
            )
            buttons[name] = button
            self.layout.addWidget(button)

        return buttons

    def _setup_button_connections(self) -> None:
        """Set up button click connections."""
        self.buttons['profile'].clicked.connect(self.open_profile)
        self.buttons['settings'].clicked.connect(self.open_settings)
        self.buttons['theme'].clicked.connect(self.toggle_theme)
        self.buttons['terminal'].clicked.connect(self.open_terminal)
        self.buttons['phone'].clicked.connect(self.open_whisper)
        self.buttons['theme'].setEnabled(False)

    def open_dialog(self, dialog_attr: str, dialog_class: type) -> None:
        """Generic method to open a popup dialog."""
        try:
            if not hasattr(self, dialog_attr):
                setattr(self, dialog_attr, dialog_class(self))
            
            dialog = getattr(self, dialog_attr)
            if not dialog.isVisible():
                dialog.center_relative_to_parent()
                dialog.show()
                
            logger.info(f"{dialog.windowTitle()} dialog opened")
            
        except Exception as e:
            logger.error(f"Error opening {dialog_class.__name__}: {e}")
            raise ActionError(f"Failed to open {dialog_class.__name__}: {str(e)}")


    def open_whisper(self) -> None:
        """Open the whisper window as a popup dialog."""
        self.open_dialog('whisper_dialog', WhisperDialog)


    def open_terminal(self) -> None:
        """Open the terminal window as a popup dialog."""
        self.open_dialog('terminal_dialog', TerminalDialog)

    def set_object_names(self) -> None:
        """Set object names for styling."""
        prefix = "phone" if self.is_phone_layout else "desktop"
        self.setObjectName(f"{prefix}HeaderSection")
        self.title.setObjectName(f"{prefix}HeaderTitle")
        
        for name, button in self.buttons.items():
            button.setObjectName(f"{prefix}HeaderButton_{name}")

    def _create_tool_button(
        self, 
        icon_key: str, 
        tooltip: str, 
        size: int
    ) -> QToolButton:
        """Create a tool button for phone layout."""
        button = QToolButton()
        self._setup_button_icon(button, icon_key, tooltip, size)
        button.setToolTip(tooltip)
        button.setMinimumSize(QSize(size, size))
        return button

    def _create_button(
        self, 
        icon_key: str, 
        tooltip: str
    ) -> QPushButton:
        """Create a regular button for desktop layout."""
        button = QPushButton()
        self._setup_button_icon(button, icon_key, tooltip)
        button.setToolTip(tooltip)
        return button

    def _setup_button_icon(
        self, 
        button: QAbstractButton, 
        icon_key: str, 
        tooltip: str,
        size: Optional[int] = None
    ) -> None:
        """Set up icon for a button."""
        icon_path = ICONS.get(icon_key, '')
        if self._is_valid_icon_path(icon_path):
            self._apply_icon_to_button(button, icon_path, size, tooltip)
        else:
            self._apply_fallback_text(button, tooltip)

    def _is_valid_icon_path(self, path: str) -> bool:
        """Check if an icon path is valid."""
        return bool(path and os.path.exists(path))

    def _apply_icon_to_button(
        self, 
        button: QAbstractButton, 
        icon_path: str, 
        size: Optional[int],
        tooltip: str
    ) -> None:
        """Apply an icon to a button."""
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            button.setIcon(QIcon(pixmap))
            if size:
                button.setIconSize(QSize(size, size))
        else:
            logger.warning(f"Icon pixmap is null for path: {icon_path}")
            self._apply_fallback_text(button, tooltip)

    def _apply_fallback_text(
        self, 
        button: QAbstractButton, 
        tooltip: str
    ) -> None:
        """Apply fallback text when icon is not available."""
        button.setText(tooltip[0])

    def update_theme(self, theme_name: str) -> None:
        """Update theme and button icons."""
        try:
            ThemeManager.apply_widget_theme(self, theme_name)
            self.update_theme_button_icon(theme_name)
        except Exception as e:
            logger.error(f"Error updating theme: {str(e)}")
            raise ThemeUpdateError(f"Failed to update theme: {str(e)}")

    def update_theme_button_icon(self, theme_name: str) -> None:
        """Update the theme toggle button icon."""
        icon_key = 'moon' if theme_name == THEME_LIGHT else 'lightbulb'
        icon_path = ICONS.get(icon_key, '')

        if self._is_valid_icon_path(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                self.buttons['theme'].setIcon(QIcon(pixmap))
                if self.is_phone_layout:
                    self.buttons['theme'].setIconSize(QSize(self.PHONE_BUTTON_SIZE, self.PHONE_BUTTON_SIZE))
            else:
                logger.warning(f"Failed to load icon for theme button: {icon_key}")
        else:
            logger.warning(f"Icon not found for theme button: {icon_key}")

    def toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        current_theme = self.parent.config.get('theme', THEME_DARK)
        new_theme = THEME_LIGHT if current_theme == THEME_DARK else THEME_DARK
        self.parent.update_theme(new_theme)

    def open_profile(self) -> None:
        """Open the profile window as a popup dialog."""
        self.open_dialog('profile_dialog', ProfileDialog)

    def open_settings(self) -> None:
        """Open the settings window as a popup dialog."""
        self.open_dialog('settings_dialog', SettingsDialog)

    def _handle_button_action(self, action_type: str) -> None:
        """Handle button action with proper logging and error handling."""
        try:
            # Placeholder for future implementation
            # Here you could add actual window opening logic
            pass
        except Exception as e:
            logger.error(f"Error handling {action_type} action: {e}")
            raise ActionError(f"Failed to handle {action_type} action: {str(e)}")

    def _apply_initial_theme(self) -> None:
        """Apply the initial theme from configuration."""
        initial_theme = self.parent.config.get('theme', THEME_DARK)
        self.update_theme(initial_theme)


class ConfigurationError(Exception):
    """Raised when required configuration is missing."""
    pass


class ThemeUpdateError(Exception):
    """Raised when theme update fails."""
    pass


class ActionError(Exception):
    """Raised when a button action fails."""
    pass