#!/usr/bin/env python3
# ./frontend/Components/Navigation/navigation_left_menu.py

import logging
import os
from typing import List, Optional
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QWidget, 
    QVBoxLayout,
    QHBoxLayout, 
    QPushButton,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    QScrollArea,
    QGroupBox,
    QToolButton
)
from Config.AppConfig.icon_config import ICONS
from Config.AppConfig.config import UI_LAYOUT_MARGINS, UI_LAYOUT_SPACING
from Styles.theme_manager import ThemeManager

logger = logging.getLogger(__name__)

class NavigationLeftMenu(QWidget):
    """
    Navigation menu component that handles page navigation and adapts to desktop/phone layouts.
    Supports collapsible sections, icons, and responsive design.
    """

    MENU_WIDTH = 300
    PHONE_BUTTON_HEIGHT = 48
    PHONE_ICON_SIZE = 24
    MENU_TITLE = "Menu"

    def __init__(self, parent: QWidget):
        """Initialize the navigation menu."""
        super().__init__(parent)
        self.parent = parent
        self._initialize_properties()
        self._setup_ui()
        self._apply_initial_theme()

    def _initialize_properties(self) -> None:
        """Initialize basic properties and state."""
        self.pages: List[str] = []
        self.is_phone_layout = self.parent.config.get('enable_phone_layout', False)
        self.is_expanded = not self.is_phone_layout
        self._verify_configuration()

    def _verify_configuration(self) -> None:
        """Verify required configuration exists."""
        required_configs = ['theme', 'enable_phone_layout']
        for config in required_configs:
            if config not in self.parent.config:
                raise ConfigurationError(f"Missing required configuration: {config}")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self._setup_base_layout()
        self._init_layout_specific_ui()
        self._set_object_names()

    def _setup_base_layout(self) -> None:
        """Set up the base layout properties."""
        self.setFixedWidth(self.MENU_WIDTH)
        self.main_layout = QVBoxLayout(self)
        self._apply_layout_settings(self.main_layout)

    def _apply_layout_settings(self, layout: QVBoxLayout) -> None:
        """Apply standard layout settings."""
        layout.setContentsMargins(*UI_LAYOUT_MARGINS)
        layout.setSpacing(UI_LAYOUT_SPACING)

    def _init_layout_specific_ui(self) -> None:
        """Initialize layout based on device type."""
        if self.is_phone_layout:
            self._init_phone_ui()
        else:
            self._init_desktop_ui()

    def _init_desktop_ui(self) -> None:
        """Initialize desktop layout UI."""
        self._setup_scroll_area()
        self._setup_title()
        self._add_spacing()
        self._init_collapsible_sections()
        self.layout.addStretch()

    def _setup_scroll_area(self) -> None:
        """Set up scrollable area for desktop layout."""
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.layout = QVBoxLayout(self.scroll_content)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area)

    def _setup_title(self) -> None:
        """Set up the menu title."""
        self.title = QLabel(self.MENU_TITLE)
        self.title.setAlignment(Qt.AlignCenter)
        if self.is_phone_layout:
            self.title.setStyleSheet("font-size: 14px;")
        (self.content_layout if self.is_phone_layout else self.layout).addWidget(self.title)

    def _add_spacing(self) -> None:
        """Add spacing after title in desktop layout."""
        self.layout.addSpacerItem(
            QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        )

    def _init_phone_ui(self) -> None:
        """Initialize phone layout UI."""
        self._setup_phone_header()
        self._setup_phone_content()

    def _setup_phone_header(self) -> None:
        """Set up the header section for phone layout."""
        header_layout = QHBoxLayout()
        self._setup_toggle_button(header_layout)
        self._setup_title()
        self.main_layout.addLayout(header_layout)

    def _setup_toggle_button(self, layout: QHBoxLayout) -> None:
        """Set up the toggle button for phone layout."""
        self.toggle_button = QToolButton()
        self.toggle_button.setIcon(QIcon(ICONS.get('menu', '')))
        self.toggle_button.clicked.connect(self.toggle_menu)
        self.toggle_button.setIconSize(QSize(self.PHONE_ICON_SIZE, self.PHONE_ICON_SIZE))
        self.toggle_button.setMinimumSize(QSize(40, 40))
        layout.addWidget(self.toggle_button)

    def _setup_phone_content(self) -> None:
        """Set up the collapsible content area for phone layout."""
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(2)
        self._init_collapsible_sections()
        self.main_layout.addWidget(self.content_widget)
        self.content_widget.setVisible(self.is_expanded)

    def _init_collapsible_sections(self) -> None:
        """Initialize the collapsible sections."""
        layout = self.content_layout if self.is_phone_layout else self.layout
        self.section = QGroupBox("Main Pages")
        self.section.setCheckable(True)
        self.section.setChecked(True)
        self.section_layout = QVBoxLayout()
        self.section_layout.setSpacing(2)
        self.section.setLayout(self.section_layout)
        layout.addWidget(self.section)

    def _set_object_names(self) -> None:
        """Set object names for styling."""
        prefix = "phone" if self.is_phone_layout else "desktop"
        self._apply_object_names(prefix)

    def _apply_object_names(self, prefix: str) -> None:
        """Apply object names with the given prefix."""
        self.setObjectName(f"{prefix}NavigationLeftMenu")
        
        if not self.is_phone_layout:
            self.scroll_area.setObjectName(f"{prefix}NavigationScrollArea")
            self.scroll_content.setObjectName(f"{prefix}NavigationScrollContent")
        
        self.title.setObjectName(f"{prefix}NavigationLeftMenuTitle")
        
        if hasattr(self, 'section'):
            self.section.setObjectName(f"{prefix}NavigationSection")
        
        if self.is_phone_layout and hasattr(self, 'toggle_button'):
            self.toggle_button.setObjectName(f"{prefix}NavigationToggleButton")

    def update_theme(self, theme_name: str) -> None:
        """Update theme for all widgets."""
        try:
            ThemeManager.apply_widget_theme(self, theme_name)
            self.create_page_buttons()
        except Exception as e:
            logger.error(f"Error updating theme: {e}")
            raise ThemeUpdateError(f"Failed to update theme: {str(e)}")

    def update_page_list(self, pages: List[str]) -> None:
        """Update the list of available pages."""
        self.pages = pages
        self.create_page_buttons()

    def create_page_buttons(self) -> None:
        """Create page buttons with appropriate sizing based on layout."""
        self._clear_existing_buttons()
        self._create_new_buttons()
        self.section_layout.addStretch()

    def _clear_existing_buttons(self) -> None:
        """Clear all existing page buttons."""
        for i in reversed(range(self.section_layout.count())):
            widget = self.section_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                self.section_layout.removeWidget(widget)
                widget.deleteLater()

    def _create_new_buttons(self) -> None:
        """Create new page buttons."""
        for page_name in self.pages:
            button = self._create_page_button(page_name)
            self._setup_button_icon(button, page_name)
            self.section_layout.addWidget(button)

    def _create_page_button(self, page_name: str) -> QPushButton:
        """Create a button for a page."""
        btn = QPushButton(page_name.replace("_", " ").capitalize())
        if self.is_phone_layout:
            btn.setMinimumHeight(self.PHONE_BUTTON_HEIGHT)
        btn.setObjectName(f"navigationButton_{page_name}")
        btn.clicked.connect(
            lambda checked=False, name=page_name: self._handle_page_click(name)
        )
        return btn

    def _setup_button_icon(self, button: QPushButton, page_name: str) -> None:
        """Set up the icon for a page button."""
        icon_key = page_name.lower()
        icon_path = ICONS.get(icon_key, '')
        
        if self._is_valid_icon_path(icon_path):
            self._apply_icon_to_button(button, icon_path)
        else:
            self._apply_default_icon(button)

    def _is_valid_icon_path(self, path: str) -> bool:
        """Check if an icon path is valid."""
        return bool(path and os.path.exists(path))

    def _apply_icon_to_button(self, button: QPushButton, icon_path: str) -> None:
        """Apply an icon to a button."""
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            button.setIcon(QIcon(pixmap))
            if self.is_phone_layout:
                button.setIconSize(QSize(self.PHONE_ICON_SIZE, self.PHONE_ICON_SIZE))
        else:
            logger.warning(f"Icon pixmap is null for path: {icon_path}")

    def _apply_default_icon(self, button: QPushButton) -> None:
        """Apply the default icon to a button."""
        default_icon_path = ICONS.get('default', '')
        if self._is_valid_icon_path(default_icon_path):
            button.setIcon(QIcon(QPixmap(default_icon_path)))

    def toggle_menu(self) -> None:
        """Toggle menu visibility in phone mode."""
        if self.is_phone_layout:
            self.is_expanded = not self.is_expanded
            self.content_widget.setVisible(self.is_expanded)
            icon_name = 'close' if self.is_expanded else 'menu'
            self.toggle_button.setIcon(QIcon(ICONS.get(icon_name, '')))

    def _handle_page_click(self, page_name: str) -> None:
        """Handle page selection with layout-specific behavior."""
        self.parent.load_page(page_name)
        if self.is_phone_layout:
            self.toggle_menu()

    def _apply_initial_theme(self) -> None:
        """Apply the initial theme from configuration."""
        initial_theme = self.parent.config.get('theme', 'dark')
        self.update_theme(initial_theme)


class ConfigurationError(Exception):
    """Raised when required configuration is missing."""
    pass


class ThemeUpdateError(Exception):
    """Raised when theme update fails."""
    pass