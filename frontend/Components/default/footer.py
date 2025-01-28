#!/usr/bin/env python3
# ./frontend/Components/default/footer.py

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QLayout
from Config.AppConfig.config import VERSION, UI_LAYOUT_MARGINS, UI_LAYOUT_SPACING
from Styles.theme_manager import ThemeManager
from log.logger import logger


class FooterFrame(QWidget):
    """
    Footer component that adapts to both desktop and phone layouts.
    Displays version information and status messages.
    """

    PHONE_FONT_SIZE = "12px"
    DEFAULT_STATUS = "By: Tobias Raanaes"
    PHONE_MARGINS = (5, 5, 5, 5)
    DESKTOP_MARGINS = (10, 5, 10, 5)

    def __init__(self, parent: QWidget):
        """Initialize the footer frame."""
        super().__init__(parent)
        self.parent = parent
        self._initialize_properties()
        self._setup_ui()
        self._apply_initial_theme()

    def _initialize_properties(self) -> None:
        """Initialize basic properties."""
        self.is_phone_layout = self.parent.config.get('enable_phone_layout', False)
        self._verify_configuration()

    def _verify_configuration(self) -> None:
        """Verify required configuration exists."""
        required_configs = ['theme', 'enable_phone_layout']
        for config in required_configs:
            if config not in self.parent.config:
                raise ConfigurationError(f"Missing required configuration: {config}")

    def _setup_ui(self) -> None:
        """Set up the user interface based on layout mode."""
        self._init_layout()
        self._create_labels()
        self.set_object_names()

    def _init_layout(self) -> None:
        """Initialize the appropriate layout based on device type."""
        layout_class = QVBoxLayout if self.is_phone_layout else QHBoxLayout
        self.layout = layout_class(self)
        self._apply_layout_settings()

    def _apply_layout_settings(self) -> None:
        """Apply layout settings based on device type."""
        margins = self.PHONE_MARGINS if self.is_phone_layout else self.DESKTOP_MARGINS
        self.layout.setContentsMargins(*margins)
        self.layout.setSpacing(UI_LAYOUT_SPACING if not self.is_phone_layout else 2)

    def _create_labels(self) -> None:
        """Create and set up the status and version labels."""
        self._setup_status_label()
        
        if not self.is_phone_layout:
            self.layout.addStretch()
            
        self._setup_version_label()

    def _setup_status_label(self) -> None:
        """Set up the status label."""
        self.status_label = QLabel(self.DEFAULT_STATUS)
        self._configure_label(self.status_label, Qt.AlignLeft if not self.is_phone_layout else Qt.AlignCenter)
        self.layout.addWidget(self.status_label)

    def _setup_version_label(self) -> None:
        """Set up the version label."""
        self.version_label = QLabel(f"Version: {VERSION}")
        self._configure_label(self.version_label, Qt.AlignRight if not self.is_phone_layout else Qt.AlignCenter)
        self.layout.addWidget(self.version_label)

    def _configure_label(self, label: QLabel, alignment: Qt.AlignmentFlag) -> None:
        """Configure a label with common settings."""
        label.setAlignment(alignment)
        if self.is_phone_layout:
            label.setStyleSheet(f"font-size: {self.PHONE_FONT_SIZE};")
            label.setWordWrap(True)

    def set_object_names(self) -> None:
        """Set object names for styling."""
        prefix = "phone" if self.is_phone_layout else "desktop"
        self.setObjectName(f"{prefix}FooterFrame")
        self.status_label.setObjectName("footerStatusLabel")
        self.version_label.setObjectName("footerVersionLabel")

    def update_theme(self, theme_name: str) -> None:
        """Update theme for all widgets."""
        try:
            ThemeManager.apply_widget_theme(self, theme_name)
        except Exception as e:
            logger.error(f"Error updating theme: {str(e)}")
            raise ThemeUpdateError(f"Failed to update theme: {str(e)}")

    def update_status(self, message: str) -> None:
        """Update status message with appropriate handling for different layouts."""
        try:
            self.status_label.setText(message)
            if self.is_phone_layout:
                self._adjust_phone_label()
        except Exception as e:
            logger.error(f"Error updating status: {str(e)}")
            raise StatusUpdateError(f"Failed to update status: {str(e)}")

    def _adjust_phone_label(self) -> None:
        """Adjust label properties for phone layout."""
        self.status_label.setWordWrap(True)
        self.status_label.adjustSize()

    def get_status(self) -> str:
        """Get current status message."""
        return self.status_label.text()

    def get_version(self) -> str:
        """Get current version text."""
        return self.version_label.text()

    def set_phone_mode(self, enabled: bool) -> None:
        """Dynamically switch between phone and desktop modes."""
        if self.is_phone_layout != enabled:
            self.is_phone_layout = enabled
            self._rebuild_ui()

    def _rebuild_ui(self) -> None:
        """Rebuild the UI after layout mode change."""
        self._clear_current_layout()
        self._setup_ui()
        self._apply_current_theme()

    def _clear_current_layout(self) -> None:
        """Clear the current layout."""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _apply_initial_theme(self) -> None:
        """Apply the initial theme from configuration."""
        self.update_theme(self.parent.config['theme'])

    def _apply_current_theme(self) -> None:
        """Apply the current theme after layout change."""
        self.update_theme(self.parent.config['theme'])


class ConfigurationError(Exception):
    """Raised when required configuration is missing."""
    pass


class ThemeUpdateError(Exception):
    """Raised when theme update fails."""
    pass


class StatusUpdateError(Exception):
    """Raised when status update fails."""
    pass