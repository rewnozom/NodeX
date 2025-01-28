#!/usr/bin/env python3
# ./frontend/Components/default/header.py

import sys
import os
from typing import Optional, Dict, Tuple
from PySide6.QtCore import Qt, QSize, QPoint
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
    QFrame,
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

class DropdownPanel(QFrame):
    """Base class for dropdown panels that appear below header buttons."""
    def __init__(self, parent=None, width=300, height=400):
        try:
            super().__init__(parent)
            self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
            self.setFixedSize(width, height)
            
            # Set up frame style
            self.setFrameShape(QFrame.StyledPanel)
            self.setFrameShadow(QFrame.Raised)
            
            self.layout = QVBoxLayout()
            self.setLayout(self.layout)
            logger.debug(f"Initialized {self.__class__.__name__} with dimensions {width}x{height}")
        except Exception as e:
            logger.error(f"Error initializing {self.__class__.__name__}: {e}")
            raise
    
    def show_under_button(self, button: QAbstractButton):
        """Position and show the panel under the given button."""
        try:
            button_pos = button.mapToGlobal(QPoint(0, 0))
            x = button_pos.x() + button.width() - self.width()
            y = button_pos.y() + button.height()
            
            self.move(x, y)
            self.show()
            logger.debug(f"Showing {self.__class__.__name__} at position ({x}, {y})")
        except Exception as e:
            logger.error(f"Error positioning {self.__class__.__name__}: {e}")
            raise

class WhisperPanel(DropdownPanel):
    def __init__(self, parent=None, whisper_hub=None):
        try:
            super().__init__(parent, width=400, height=500)
            if whisper_hub is None:
                logger.error("WhisperHub instance must be provided")
                raise ValueError("WhisperHub instance must be provided")
            self.whisper_hub = whisper_hub
            self.whisper_widget = self.whisper_hub.whisper_tab
            self.layout.addWidget(self.whisper_widget)
            logger.debug("WhisperPanel initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing WhisperPanel: {e}")
            raise

    def closeEvent(self, event):
        try:
            # Clean up resources properly
            if hasattr(self, 'whisper_widget'):
                self.whisper_widget.cleanup()
            if hasattr(self, 'whisper_hub'):
                del self.whisper_hub
            super().closeEvent(event)
            logger.debug("WhisperPanel closed and cleaned up")
        except Exception as e:
            logger.error(f"Error closing WhisperPanel: {e}")
            event.accept()

class ProfilePanel(DropdownPanel):
    def __init__(self, parent=None):
        try:
            super().__init__(parent, width=300, height=400)
            self.layout.addWidget(QLabel("Profile Content"))
            logger.debug("ProfilePanel initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ProfilePanel: {e}")
            raise

class SettingsPanel(DropdownPanel):
    def __init__(self, parent=None):
        try:
            super().__init__(parent, width=300, height=400)
            self.layout.addWidget(QLabel("Settings Content"))
            logger.debug("SettingsPanel initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing SettingsPanel: {e}")
            raise

class TerminalPanel(DropdownPanel):
    def __init__(self, parent=None):
        try:
            super().__init__(parent, width=400, height=500)
            self.layout.addWidget(QLabel("Terminal Content"))
            logger.debug("TerminalPanel initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing TerminalPanel: {e}")
            raise

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
        try:
            super().__init__(parent)
            self.parent = parent
            # Initialize WhisperHub early
            self.whisper_hub = WhisperHub()
            logger.debug("WhisperHub initialized during HeaderSection creation")
            self._initialize_properties()
            self._setup_ui()
            self._apply_initial_theme()
            logger.debug("HeaderSection initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing HeaderSection: {e}")
            raise

    def set_object_names(self) -> None:
        """Set object names for styling."""
        prefix = "phone" if self.is_phone_layout else "desktop"
        self.setObjectName(f"{prefix}HeaderSection")
        self.title.setObjectName(f"{prefix}HeaderTitle")
        
        for name, button in self.buttons.items():
            button.setObjectName(f"{prefix}HeaderButton_{name}")

    def _initialize_properties(self) -> None:
        """Initialize basic properties."""
        try:
            self.is_phone_layout = self.parent.config.get('enable_phone_layout', False)
            self.button_size = self.PHONE_BUTTON_SIZE if self.is_phone_layout else self.DESKTOP_BUTTON_SIZE
            self._verify_configuration()
            logger.debug(f"Properties initialized with phone_layout={self.is_phone_layout}")
        except Exception as e:
            logger.error(f"Error initializing properties: {e}")
            raise

    def _verify_configuration(self) -> None:
        """Verify required configuration exists."""
        try:
            required_configs = ['theme', 'enable_phone_layout']
            for config in required_configs:
                if config not in self.parent.config:
                    logger.error(f"Missing required configuration: {config}")
                    raise ConfigurationError(f"Missing required configuration: {config}")
            logger.debug("Configuration verified successfully")
        except Exception as e:
            logger.error(f"Error verifying configuration: {e}")
            raise

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        try:
            self._init_layout()
            self._setup_title()
            self._add_spacer()
            self._init_buttons()
            self.set_object_names()
            logger.debug("UI setup completed")
        except Exception as e:
            logger.error(f"Error setting up UI: {e}")
            raise

    def _init_layout(self) -> None:
        """Initialize the layout."""
        try:
            self.layout = QHBoxLayout(self)
            self.layout.setContentsMargins(*UI_LAYOUT_MARGINS)
            self.layout.setSpacing(UI_LAYOUT_SPACING)
            logger.debug("Layout initialized")
        except Exception as e:
            logger.error(f"Error initializing layout: {e}")
            raise



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
        """Open the profile window."""
        logger.info("Profile window opened")
        self._handle_button_action("profile")

    def open_settings(self) -> None:
        """Open the settings window."""
        logger.info("Settings window opened")
        self._handle_button_action("settings")

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

    def _setup_title(self) -> None:
        """Set up the title label."""
        try:
            self.title = QLabel(APP_NAME)
            if self.is_phone_layout:
                self.title.setStyleSheet(f"font-size: {self.PHONE_FONT_SIZE};")
            self.layout.addWidget(self.title)
            logger.debug("Title setup completed")
        except Exception as e:
            logger.error(f"Error setting up title: {e}")
            raise

    def _add_spacer(self) -> None:
        """Add spacing to push buttons to the right."""
        try:
            spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            self.layout.addItem(spacer)
            logger.debug("Spacer added to layout")
        except Exception as e:
            logger.error(f"Error adding spacer: {e}")
            raise

    def _init_buttons(self) -> None:
        """Initialize header buttons based on layout mode."""
        try:
            self.buttons = self._create_buttons()
            self._setup_button_connections()
            logger.debug("Buttons initialized and connected")
        except Exception as e:
            logger.error(f"Error initializing buttons: {e}")
            raise


    def _setup_button_connections(self) -> None:
        """Set up button click connections."""
        try:
            self.buttons['profile'].clicked.connect(self.toggle_profile)
            self.buttons['settings'].clicked.connect(self.toggle_settings)
            self.buttons['theme'].clicked.connect(self.toggle_theme)
            self.buttons['terminal'].clicked.connect(self.toggle_terminal)
            self.buttons['phone'].clicked.connect(self.toggle_whisper)
            self.buttons['theme'].setEnabled(False)
            logger.debug("Button connections established")
        except Exception as e:
            logger.error(f"Error setting up button connections: {e}")
            raise

    def toggle_panel(self, panel_attr: str, panel_class: type, button: QAbstractButton) -> None:
        """Generic method to toggle a dropdown panel."""
        try:
            if not hasattr(self, panel_attr):
                if panel_class == WhisperPanel:
                    # Pass the already initialized WhisperHub instance
                    setattr(self, panel_attr, panel_class(self, whisper_hub=self.whisper_hub))
                else:
                    setattr(self, panel_attr, panel_class(self))
            
            panel = getattr(self, panel_attr)
            if panel.isVisible():
                panel.hide()
                logger.info(f"{panel_class.__name__} panel hidden")
            else:
                self.hide_all_panels()
                panel.show_under_button(button)
                logger.info(f"{panel_class.__name__} panel shown")
                
        except Exception as e:
            logger.error(f"Error toggling {panel_class.__name__}: {e}")
            raise ActionError(f"Failed to toggle {panel_class.__name__}: {str(e)}")

    def hide_all_panels(self):
        """Hide all dropdown panels."""
        try:
            panels = ['whisper_panel', 'profile_panel', 'settings_panel', 'terminal_panel']
            for panel_name in panels:
                if hasattr(self, panel_name):
                    getattr(self, panel_name).hide()
            logger.debug("All panels hidden")
        except Exception as e:
            logger.error(f"Error hiding panels: {e}")
            raise

    def toggle_whisper(self) -> None:
        """Toggle the whisper panel."""
        try:
            self.toggle_panel('whisper_panel', WhisperPanel, self.buttons['phone'])
            logger.info("Whisper panel toggled")
        except Exception as e:
            logger.error(f"Error toggling whisper panel: {e}")
            raise ActionError(f"Failed to toggle whisper panel: {str(e)}")

    def toggle_profile(self) -> None:
        """Toggle the profile panel."""
        try:
            self.toggle_panel('profile_panel', ProfilePanel, self.buttons['profile'])
            logger.info("Profile panel toggled")
        except Exception as e:
            logger.error(f"Error toggling profile panel: {e}")
            raise ActionError(f"Failed to toggle profile panel: {str(e)}")

    def toggle_settings(self) -> None:
        """Toggle the settings panel."""
        try:
            self.toggle_panel('settings_panel', SettingsPanel, self.buttons['settings'])
            logger.info("Settings panel toggled")
        except Exception as e:
            logger.error(f"Error toggling settings panel: {e}")
            raise ActionError(f"Failed to toggle settings panel: {str(e)}")

    def toggle_terminal(self) -> None:
        """Toggle the terminal panel."""
        try:
            self.toggle_panel('terminal_panel', TerminalPanel, self.buttons['terminal'])
            logger.info("Terminal panel toggled")
        except Exception as e:
            logger.error(f"Error toggling terminal panel: {e}")
            raise ActionError(f"Failed to toggle terminal panel: {str(e)}")

    # [Previous methods remain the same: _create_tool_button, _create_button, _setup_button_icon, 
    # _is_valid_icon_path, _apply_icon_to_button, _apply_fallback_text, update_theme, 
    # update_theme_button_icon, toggle_theme, _apply_initial_theme]

class ConfigurationError(Exception):
    """Raised when required configuration is missing."""
    pass

class ThemeUpdateError(Exception):
    """Raised when theme update fails."""
    pass

class ActionError(Exception):
    """Raised when a button action fails."""
    pass
