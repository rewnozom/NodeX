#!/usr/bin/env python3
# ./frontend/DynamicMain/page_manager.py

import os
import json
import importlib
from typing import Optional, Any, Dict, List
from PySide6.QtWidgets import QStackedWidget, QMessageBox
from Config.AppConfig.config import ConfigManager
from Config.AppConfig.config import *
from log.logger import logger
from Styles.theme_manager import ThemeManager
from Utils.loader import load_module, get_subdirectories
from .page_state_handler import PageStateHandler

class PageManager:
    def __init__(self, main_window):
        logger.info("Initializing PageManager...")
        self.main_window = main_window
        self.base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        try:
            self._verify_config()
            self.state_handler = PageStateHandler()
            logger.info("PageManager initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing PageManager: {e}")
            self.state_handler = None

    def _verify_config(self) -> None:
        logger.debug("Verifying configuration...")
        required_configs = [
            'desktop_layout_dir',
            'android_layout_dir',
            'enable_phone_layout',
            'last_page_key'
        ]
        for config in required_configs:
            if config not in self.main_window.config:
                logger.error(f"Missing required configuration: {config}")
                raise ConfigurationError(f"Missing required configuration: {config}")
        logger.debug("Configuration verification completed")

    def _get_layout_dir(self) -> str:
        is_phone = self.main_window.config['enable_phone_layout']
        config_key = 'android_layout_dir' if is_phone else 'desktop_layout_dir'
        layout_dir = self.main_window.config[config_key]

        if layout_dir.startswith('./'):
            layout_dir = os.path.abspath(layout_dir)
        logger.debug(f"Using layout directory: {layout_dir}")
        return layout_dir

    def _build_module_path(self, layout_dir: str, page_dir: str) -> str:
        layout_type = 'android' if self.main_window.config['enable_phone_layout'] else 'desktop'
        module_path = f"frontend.Pages.{layout_type}.Layout.{page_dir}.Page"
        logger.debug(f"Built module path: {module_path}")
        return module_path

    def discover_pages(self) -> None:
        """
        Discover available page directories and attempt to load them immediately.
        If you prefer a lazy-load approach, comment out the immediate module load
        and store only directory names here.
        """
        logger.info("Starting page discovery process...")

        layout_dir = self._get_layout_dir()
        if not os.path.isdir(layout_dir):
            logger.error(f"Layout directory does not exist: {layout_dir}")
            self._handle_error("no_pages_available", f"Layout directory '{layout_dir}' does not exist.")
            return

        # Get subdirectories, but skip non-page directories like __pycache__, venv, etc.
        all_subdirs = get_subdirectories(layout_dir)
        page_dirs = [d for d in all_subdirs if d not in {"__pycache__", "venv"}]
        logger.debug(f"Found page directories: {page_dirs}")

        discovered_pages = self._process_page_directories(layout_dir, page_dirs)
        if discovered_pages:
            self.main_window.navigation.update_page_list(list(discovered_pages.keys()))
            logger.info(f"Added {len(discovered_pages)} pages to navigation menu")
        else:
            logger.error("No pages discovered")
            self._handle_error("no_pages_discovered")

        logger.info("Page discovery completed")

    # ------------------------------------------------------------------------
    # Example lazy loading approach

    # def discover_pages(self) -> None:
    #     logger.info("Starting (LAZY) page discovery process...")
    #     layout_dir = self._get_layout_dir()
    #     if not os.path.isdir(layout_dir):
    #         self._handle_error("no_pages_available", f"Layout dir '{layout_dir}' does not exist.")
    #         return
    #
    #     all_subdirs = get_subdirectories(layout_dir)
    #     page_dirs = [d for d in all_subdirs if d not in {"__pycache__", "venv"}]
    #     self.main_window.available_page_dirs = page_dirs  # Store only directories
    #     self.main_window.navigation.update_page_list(page_dirs)
    #     logger.info(f"Discovered {len(page_dirs)} page directories. Lazy load enabled.")
    # ------------------------------------------------------------------------

    def _process_page_directories(self, layout_dir: str, page_dirs: List[str]) -> Dict[str, Any]:
        discovered_pages = {}
        for page_dir in page_dirs:
            try:
                module_path = self._build_module_path(layout_dir, page_dir)
                module = load_module(module_path)
                if module and hasattr(module, 'Page'):
                    discovered_pages[page_dir] = module
                    self.main_window.available_pages[page_dir] = module
                    logger.info(f"Page '{page_dir}' discovered and loaded")
                else:
                    logger.warning(f"Module '{module_path}' missing Page class")
            except Exception as e:
                logger.error(f"Error discovering page '{page_dir}': {e}")
        return discovered_pages

    def load_page(self, page_name: str) -> bool:
        logger.info(f"Attempting to load page: {page_name}")

        if not self._validate_page_exists(page_name):
            # If the user tried to load a page that doesn't exist, fall back
            # to the first available page.
            return self.load_first_available_page()

        # If we've already instantiated the page, just show it
        if page_name in self.main_window.loaded_pages:
            logger.debug(f"Page '{page_name}' already loaded, showing existing instance")
            self.show_page(page_name)
            return True

        return self._initialize_new_page(page_name)

    def _validate_page_exists(self, page_name: str) -> bool:
        if page_name not in self.main_window.available_pages:
            logger.error(f"Page '{page_name}' not found in available pages")
            self._handle_error("page_not_found", page_name=page_name)
            return False
        return True

    def _initialize_new_page(self, page_name: str) -> bool:
        try:
            module = self.main_window.available_pages[page_name]
            page_class = getattr(module, 'Page', None)

            if not page_class:
                raise AttributeError(f"No 'Page' class found in '{page_name}'")

            logger.debug(f"Creating new instance of page '{page_name}'")
            page_instance = page_class(self.main_window)
            self.main_window.loaded_pages[page_name] = page_instance
            self.main_window.stacked_widget.addWidget(page_instance)

            self._apply_theme_to_page(page_instance)
            self.show_page(page_name)
            self._save_last_page(page_name)

            logger.info(f"Successfully initialized page '{page_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize page '{page_name}': {e}")
            self._handle_error("failed_to_load_page", page_name=page_name, error_msg=str(e))
            return False

    def _apply_theme_to_page(self, page_instance: Any) -> None:
        try:
            if hasattr(page_instance, 'update_theme'):
                page_instance.update_theme(self.main_window.config['theme'])
            else:
                ThemeManager.apply_widget_theme(page_instance, self.main_window.config['theme'])
            logger.debug("Theme applied successfully to page")
        except Exception as e:
            logger.error(f"Error applying theme to page: {e}")

    def _save_last_page(self, page_name: str) -> None:
        try:
            if self.state_handler:
                self.state_handler.save_last_page(page_name)
                logger.debug(f"Saved '{page_name}' as last page in state file")
            else:
                # fallback to config if no state_handler
                self.main_window.config_manager.settings.setValue(
                    self.main_window.config['last_page_key'],
                    page_name
                )
                logger.debug(f"Saved '{page_name}' as last page in settings")
        except Exception as e:
            logger.error(f"Error saving last page state: {e}")

    def show_page(self, page_name: str) -> None:
        if not self._validate_loaded_page(page_name):
            return

        page_instance = self.main_window.loaded_pages[page_name]
        index = self.main_window.stacked_widget.indexOf(page_instance)

        if index == -1:
            logger.error(f"Page '{page_name}' not found in stacked widget")
            self.main_window.error_handler.show_error_message(
                f"Page '{page_name}' cannot be displayed."
            )
            return

        self.main_window.stacked_widget.setCurrentIndex(index)
        logger.debug(f"Switched to page '{page_name}' at index {index}")

        self._handle_page_load_event(page_instance, page_name)

    def _validate_loaded_page(self, page_name: str) -> bool:
        if page_name not in self.main_window.loaded_pages:
            logger.error(f"Page '{page_name}' not loaded")
            self.main_window.error_handler.show_error_message(
                f"Page '{page_name}' is not loaded."
            )
            return False
        return True

    def _handle_page_load_event(self, page_instance: Any, page_name: str) -> None:
        if hasattr(page_instance, 'on_load'):
            try:
                page_instance.on_load()
                logger.debug(f"Executed on_load for page '{page_name}'")
            except Exception as e:
                logger.error(f"Error in on_load for page '{page_name}': {e}")
                self.main_window.error_handler.show_error_message(
                    f"Error loading page '{page_name}'.",
                    str(e)
                )

    def load_last_page(self) -> None:
        logger.info("Attempting to load last used page")
        try:
            last_page = None
            if self.state_handler:
                last_page = self.state_handler.get_last_page()
                logger.debug(f"Retrieved last page from state handler: {last_page}")
            else:
                last_page = self.main_window.config.get('last_page')
                logger.debug(f"Retrieved last page from config: {last_page}")

            if last_page and last_page in self.main_window.available_pages:
                if self.load_page(last_page):
                    logger.info(f"Successfully loaded last page: {last_page}")
                else:
                    logger.warning("Failed to load last page, loading first available")
                    self.load_first_available_page()
            else:
                if last_page:
                    logger.warning(f"Last page '{last_page}' not found")
                else:
                    logger.info("No last page saved")
                self.load_first_available_page()
        except Exception as e:
            logger.error(f"Error loading last page: {e}")
            self.load_first_available_page()

    def load_first_available_page(self) -> bool:
        logger.info("Attempting to load first available page")
        if not self.main_window.available_pages:
            logger.error("No pages available to load")
            self._handle_error("no_pages_available")
            return False

        first_page = next(iter(self.main_window.available_pages))
        logger.debug(f"Loading first available page: {first_page}")
        return self.load_page(first_page)

    def remove_page(self, page_name: str) -> None:
        """
        Remove page_name from both available_pages and loaded_pages.
        Call on_unload if present, and remove widget from stacked_widget.
        """
        # First check if it's loaded
        if page_name in self.main_window.loaded_pages:
            page_instance = self.main_window.loaded_pages[page_name]
            # Let the page handle its own cleanup
            if hasattr(page_instance, 'on_unload'):
                try:
                    page_instance.on_unload()
                    logger.debug(f"Called on_unload for page '{page_name}'")
                except Exception as e:
                    logger.error(f"Error calling on_unload on page '{page_name}': {e}")

            # Remove from the stacked widget
            index = self.main_window.stacked_widget.indexOf(page_instance)
            if index != -1:
                self.main_window.stacked_widget.removeWidget(page_instance)
                logger.debug(f"Removed page '{page_name}' from QStackedWidget")

            del self.main_window.loaded_pages[page_name]
            logger.debug(f"Removed '{page_name}' from loaded_pages")

        # Now remove from available_pages if we never want to see it again
        if page_name in self.main_window.available_pages:
            del self.main_window.available_pages[page_name]
            logger.debug(f"Removed '{page_name}' from available_pages")

        # Update last page if needed
        if self.state_handler and self.state_handler.get_last_page() == page_name:
            self.state_handler.save_last_page("")
        elif self.main_window.config.get('last_page') == page_name:
            self.main_window.config['last_page'] = ""
            self.main_window.config_manager.settings.setValue('last_page', "")

        logger.info(f"Page '{page_name}' removed successfully")

    def cleanup(self):
        """
        Clean up all loaded pages and release resources before application exit.
        """
        logger.info("Cleaning up PageManager...")

        for page_name, page_instance in list(self.main_window.loaded_pages.items()):
            if hasattr(page_instance, 'on_unload'):
                try:
                    page_instance.on_unload()
                    logger.debug(f"Called on_unload for page '{page_name}'")
                except Exception as e:
                    logger.error(f"Error calling on_unload on page '{page_name}': {e}")

            # Remove from stacked widget
            index = self.main_window.stacked_widget.indexOf(page_instance)
            if index != -1:
                self.main_window.stacked_widget.removeWidget(page_instance)
                logger.debug(f"Removed page '{page_name}' from QStackedWidget")

        # Clear references
        self.main_window.loaded_pages.clear()
        logger.debug("Cleared loaded_pages dictionary")

        logger.info("PageManager cleanup complete.")

    def get_current_page(self) -> Optional[Any]:
        current_widget = self.main_window.stacked_widget.currentWidget()
        page_class = self._get_page_class()
        return current_widget if page_class and isinstance(current_widget, page_class) else None

    def _get_page_class(self) -> Optional[type]:
        try:
            for module in self.main_window.available_pages.values():
                if hasattr(module, 'Page'):
                    return module.Page
            logger.warning("No Page class found in available modules")
        except Exception as e:
            logger.error(f"Error retrieving Page class: {e}")
        return None

    def _handle_error(self, error_key: str, custom_message: str = None, **kwargs) -> None:
        try:
            error_message = self.main_window.config['error_messages'][error_key].format(**kwargs)
            if custom_message:
                error_message = f"{custom_message} {error_message}"
            logger.error(error_message)
            self.main_window.error_handler.show_error_message(error_message)
        except Exception as e:
            logger.error(f"Error handling error message: {e}")


class ConfigurationError(Exception):
    pass
