#!/usr/bin/env python3
# ./frontend/DynamicMain/ui_setup.py

from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
   QWidget, 
   QVBoxLayout, 
   QHBoxLayout, 
   QStackedWidget
)
from Config.AppConfig.config import (
   ConfigManager, 
   UI_LAYOUT_MARGINS, 
   UI_LAYOUT_SPACING
)
from frontend.DynamicMain.icon_manager import IconManager
from frontend.Components.default.footer import FooterFrame
from frontend.Components.default.header import HeaderSection
from frontend.Components.Navigation.navigation_left_menu import NavigationLeftMenu
from Styles.theme_manager import ThemeManager
from log.logger import logger

class UISetup:
   def __init__(self, main_window):
       self.main_window = main_window
       self.icon_manager = IconManager(self.main_window)
       self._verify_config()

   def _verify_config(self) -> None:
       required_configs = [
           'app_name',
           'window_size',
           'theme'
       ]
       for config in required_configs:
           if config not in self.main_window.config:
               raise ConfigurationError(f"Missing required configuration: {config}")

   def init_ui(self) -> None:
       try:
           logger.info("Initializing UI...")
           self._setup_window_properties()
           self._initialize_layout_structure()
           self._finalize_setup()
           logger.info("UI initialization complete.")
       except Exception as e:
           logger.error(f"Error during UI initialization: {e}")
           raise UIInitializationError(f"Failed to initialize UI: {str(e)}")

   def _setup_window_properties(self) -> None:
       self.main_window.setWindowTitle(self.main_window.config['app_name'])
       self.main_window.resize(self.main_window.config['window_size'])

   def _initialize_layout_structure(self) -> None:
       self.setup_central_widget()
       self.setup_container()
       self.setup_header()
       self.setup_content()
       self.setup_footer()
       self.main_window.main_layout.addWidget(self.main_window.container)

   def _finalize_setup(self) -> None:
       self.set_object_names()
       self.apply_current_theme()
       self.icon_manager.setup_icons()

   def setup_central_widget(self) -> None:
       try:
           self.main_window.central_widget = QWidget()
           self.main_window.setCentralWidget(self.main_window.central_widget)
           self.main_window.main_layout = QVBoxLayout(self.main_window.central_widget)
           self._apply_layout_settings(self.main_window.main_layout)
           logger.debug("Main layout initialized")
       except Exception as e:
           logger.error(f"Error setting up central widget: {e}")
           raise

   def setup_container(self) -> None:
       try:
           self.main_window.container = QWidget()
           self.main_window.container_layout = QVBoxLayout(self.main_window.container)
           self._apply_layout_settings(self.main_window.container_layout)
           logger.debug("Container layout initialized")
       except Exception as e:
           logger.error(f"Error setting up container: {e}")
           raise

   def setup_header(self) -> None:
       try:
           self.main_window.header = HeaderSection(self.main_window)
           self.main_window.container_layout.addWidget(self.main_window.header)
           logger.debug("Header section added")
       except Exception as e:
           logger.error(f"Error setting up header: {e}")
           raise

   def setup_content(self) -> None:
       try:
           self._create_content_widget()
           self._setup_navigation()
           self._setup_stacked_widget()
           self._configure_content_layout()
           logger.debug("Content area setup complete")
       except Exception as e:
           logger.error(f"Error setting up content: {e}")
           raise

   def _create_content_widget(self) -> None:
       self.main_window.content_widget = QWidget()
       self.main_window.content_layout = QHBoxLayout(self.main_window.content_widget)
       self.main_window.content_layout.setContentsMargins(0, 0, 0, 0)
       self.main_window.content_layout.setSpacing(UI_LAYOUT_SPACING)

   def _setup_navigation(self) -> None:
       self.main_window.navigation = NavigationLeftMenu(self.main_window)
       self.main_window.content_layout.addWidget(self.main_window.navigation)

   def _setup_stacked_widget(self) -> None:
       self.main_window.stacked_widget = QStackedWidget()
       self.main_window.content_layout.addWidget(self.main_window.stacked_widget)

   def _configure_content_layout(self) -> None:
       self.main_window.content_layout.setStretch(0, 1)
       self.main_window.content_layout.setStretch(1, 4)
       self.main_window.container_layout.addWidget(self.main_window.content_widget)

   def setup_footer(self) -> None:
       try:
           self.main_window.footer = FooterFrame(self.main_window)
           self.main_window.container_layout.addWidget(self.main_window.footer)
           logger.debug("Footer section added")
       except Exception as e:
           logger.error(f"Error setting up footer: {e}")
           raise

   def _apply_layout_settings(self, layout: QVBoxLayout) -> None:
       layout.setContentsMargins(*UI_LAYOUT_MARGINS)
       layout.setSpacing(UI_LAYOUT_SPACING)

   def set_object_names(self) -> None:
       object_names = {
           'central_widget': "centralWidget",
           'container': "container",
           'content_widget': "content", 
           'navigation': "navigationLeftMenu",
           'stacked_widget': "stackedWidget",
           'header': "headerSection",
           'footer': "footerFrame"
       }
       for attr, name in object_names.items():
           if hasattr(self.main_window, attr):
               widget = getattr(self.main_window, attr)
               widget.setObjectName(name)

   def apply_current_theme(self) -> None:
       try:
           theme_name = self.main_window.config['theme']
           self._apply_theme_to_components(theme_name)
           self._update_loaded_pages_theme(theme_name)
           self._apply_code_block_styles()
           logger.info(f"Theme '{theme_name}' applied successfully.")
       except Exception as e:
           logger.error(f"Error applying theme: {e}")
           if hasattr(self.main_window, 'error_handler'):
               self.main_window.error_handler.show_error_message(
                   "Failed to apply theme", 
                   str(e)
               )

   def _apply_theme_to_components(self, theme_name: str) -> None:
       ThemeManager.apply_theme(theme_name)
       ThemeManager.update_main_window(self.main_window, theme_name)
       ThemeManager.update_header_section(self.main_window.header, theme_name)
       ThemeManager.update_navigation_left_menu(self.main_window.navigation, theme_name)
       ThemeManager.update_footer_frame(self.main_window.footer, theme_name)

   def _update_loaded_pages_theme(self, theme_name: str) -> None:
       if hasattr(self.main_window, 'loaded_pages'):
           for page_instance in self.main_window.loaded_pages.values():
               if hasattr(page_instance, 'update_theme'):
                   page_instance.update_theme(theme_name)
               else:
                   ThemeManager.apply_widget_theme(page_instance, theme_name)

   def _apply_code_block_styles(self) -> None:
       ThemeManager.apply_code_block_style_to_all(
           ThemeManager.get_theme().get('CODE_BLOCK_STYLE', {})
       )

class ConfigurationError(Exception):
   pass

class UIInitializationError(Exception):
   pass
