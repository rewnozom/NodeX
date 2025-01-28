# ./shared/layout/layout_manager.py

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QSplitter
)
from typing import Optional

class LayoutManager:
    """Manages responsive layout switching between desktop and phone modes."""
    
    def __init__(self, main_window: QMainWindow):
        self.main_window = main_window
        self.is_phone_layout = main_window.config.get('enable_phone_layout', False)
        self.setup_layout()
        
        # Store references to widgets
        self.central_widget = None
        self.main_layout = None
        self.container = None
        self.container_layout = None
        self.header_section = None
        self.content_widget = None
        self.navigation = None
        self.stacked_widget = None
        self.footer_frame = None
        
    def setup_layout(self):
        """Initialize the appropriate layout based on configuration."""
        if self.is_phone_layout:
            self._setup_phone_layout()
        else:
            self._setup_desktop_layout()
            
        self._setup_common_elements()
        
    def _setup_phone_layout(self):
        """Setup mobile-friendly vertical layout."""
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.main_window.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create container
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        
        # Add header
        from frontend.Components.default.header import Header_Section
        self.header_section = Header_Section(self.main_window)
        self.container_layout.addWidget(self.header_section)
        
        # Create content area
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Add navigation (collapsible in phone mode)
        from frontend.Components.Navigation.navigation_phone import Navigation_Phone_Menu
        self.navigation = Navigation_Phone_Menu(self.main_window)
        content_layout.addWidget(self.navigation)
        
        # Add stacked widget for pages
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        
        self.container_layout.addWidget(self.content_widget)
        
        # Add footer
        from frontend.Components.default.footer import Footer_frame
        self.footer_frame = Footer_frame(self.main_window)
        self.container_layout.addWidget(self.footer_frame)
        
        self.main_layout.addWidget(self.container)
        
    def _setup_desktop_layout(self):
        """Setup traditional desktop layout."""
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.main_window.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create container
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        
        # Add header
        from frontend.Components.default.header import Header_Section
        self.header_section = Header_Section(self.main_window)
        self.container_layout.addWidget(self.header_section)
        
        # Create content area with horizontal layout
        self.content_widget = QWidget()
        content_layout = QHBoxLayout(self.content_widget)
        
        # Add navigation
        from frontend.Components.Navigation.navigation_left_menu import Navigation_Left_Menu
        self.navigation = Navigation_Left_Menu(self.main_window)
        content_layout.addWidget(self.navigation)
        
        # Add stacked widget for pages
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        
        # Set content stretch factors
        content_layout.setStretch(0, 1)
        content_layout.setStretch(1, 4)
        
        self.container_layout.addWidget(self.content_widget)
        
        # Add footer
        from frontend.Components.default.footer import Footer_frame
        self.footer_frame = Footer_frame(self.main_window)
        self.container_layout.addWidget(self.footer_frame)
        
        self.main_layout.addWidget(self.container)
        
    def _setup_common_elements(self):
        """Setup elements common to both layouts."""
        # Set object names for styling
        self._set_object_names()
        
        # Apply current theme
        self._apply_theme()
        
    def _set_object_names(self):
        """Set object names for styling."""
        layout_prefix = "phone" if self.is_phone_layout else "desktop"
        
        self.central_widget.setObjectName(f"{layout_prefix}CentralWidget")
        self.container.setObjectName(f"{layout_prefix}Container")
        self.content_widget.setObjectName(f"{layout_prefix}Content")
        self.navigation.setObjectName(f"{layout_prefix}Navigation")
        self.stacked_widget.setObjectName(f"{layout_prefix}StackedWidget")
        self.header_section.setObjectName(f"{layout_prefix}HeaderSection")
        self.footer_frame.setObjectName(f"{layout_prefix}FooterFrame")
        
    def _apply_theme(self):
        """Apply the current theme to all widgets."""
        from Styles.theme_manager import ThemeManager
        theme_name = self.main_window.config.get('theme', 'dark')
        
        ThemeManager.apply_theme(theme_name)
        ThemeManager.update_main_window(self.main_window, theme_name)
        ThemeManager.update_header_section(self.header_section, theme_name)
        ThemeManager.update_navigation_left_menu(self.navigation, theme_name)  # Fixed method name here
        ThemeManager.update_footer_frame(self.footer_frame, theme_name)
        
    def get_layout_type(self) -> str:
        """Return the current layout type."""
        return "phone" if self.is_phone_layout else "desktop"