#!/usr/bin/env python3
# dynamic_main_ref.py

import sys
from typing import Optional, Any, NoReturn
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtCore import QSize, qInstallMessageHandler
from frontend.DynamicMain.logger_setup import setup_logger
from log.logger import logger, ic, qt_message_handler
from Styles.theme_manager import ThemeManager
from Config.AppConfig.config import (
    ConfigManager, 
    THEME_OPTIONS, 
    CURRENT_THEME,
    WINDOW_WIDTH,
    WINDOW_HEIGHT
)

class MainWindow(QMainWindow):
    """
    Main application window handling the core application functionality.
    Manages UI components, page loading, and theme handling.
    """

    def __init__(self):
        """Initialize the main window and its components."""
        super().__init__()
        self._initialize_application()

    def _initialize_application(self) -> None:
        """Initialize all application components with proper error handling."""
        try:
            self._setup_configuration()
            self._configure_window()
            self._initialize_components()
            self._setup_application()
        except Exception as e:
            self._handle_initialization_error(e)

    def _setup_configuration(self) -> None:
        """Initialize and load configuration settings."""
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config

    def _configure_window(self) -> None:
        """Configure initial window properties."""
        self.setWindowTitle(self.config.get('app_name', "Application"))
        self._setup_window_size()

    def _setup_window_size(self) -> None:
        """Set up the window size based on configuration."""
        default_size = QSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        window_size = self.config.get('window_size', default_size)
        
        if isinstance(window_size, QSize):
            self.resize(window_size)
            logger.debug(f"Window resized to: {window_size.width()}x{window_size.height()}")
        else:
            logger.warning(f"Invalid window_size type. Using default size {WINDOW_WIDTH}x{WINDOW_HEIGHT}.")
            self.resize(default_size)

    def _initialize_components(self) -> None:
        """Initialize all main application components."""
        try:
            # Initialize core components
            from frontend.DynamicMain.error_handler import ErrorHandler
            from frontend.DynamicMain.ui_setup import UISetup
            from frontend.DynamicMain.page_manager import PageManager
            from frontend.DynamicMain.keybindings import KeyBindings

            self.error_handler = ErrorHandler(self)
            self.ui_setup = UISetup(self)
            self.page_manager = PageManager(self)
            self.keybindings = KeyBindings(self)

            # Initialize storage dictionaries
            self.loaded_pages = {}
            self.available_pages = {}
            self.module_cache = {}
            
            logger.info("All components initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise ComponentInitializationError(f"Failed to initialize components: {str(e)}")

    def _setup_application(self) -> None:
        """Set up the application UI and functionality."""
        try:
            self.ui_setup.init_ui()
            self.page_manager.discover_pages()
            self.page_manager.load_last_page()
            self.keybindings.init_keybindings()
        except Exception as e:
            logger.error(f"Error during application setup: {e}")
            raise ApplicationSetupError(f"Failed to setup application: {str(e)}")

    def _handle_initialization_error(self, error: Exception) -> None:
        """Handle errors during initialization."""
        logger.error(f"An error occurred during initialization: {error}")
        if hasattr(self, 'error_handler'):
            self.error_handler.show_error_message(
                "An error occurred during application initialization.",
                str(error)
            )
        else:
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"An error occurred during application initialization: {str(error)}"
            )
        self.close()

    def load_page(self, page_name: str) -> bool:
        """Load a page by name with proper error handling."""
        try:
            result = self.page_manager.load_page(page_name)
            if result:
                logger.info(f"Page '{page_name}' loaded successfully.")
            else:
                logger.error(f"Failed to load page '{page_name}'.")
            return result
        except Exception as e:
            logger.error(f"Error loading page '{page_name}': {e}")
            self.error_handler.show_error_message(
                f"Error loading page '{page_name}'",
                str(e)
            )
            return False

    def update_theme(self, new_theme: str) -> None:
        """Update the application theme with proper error handling."""
        try:
            if new_theme in THEME_OPTIONS:
                self._apply_theme(new_theme)
            else:
                logger.warning(f"Invalid theme '{new_theme}'. Using default theme '{CURRENT_THEME}'.")
                self._apply_theme(CURRENT_THEME)
        except Exception as e:
            logger.error(f"Error updating theme: {e}")
            self.error_handler.show_error_message(
                "Theme Update Error",
                f"Failed to update theme to '{new_theme}': {str(e)}"
            )

    def _apply_theme(self, theme_name: str) -> None:
        """Apply the specified theme to the application."""
        self.config['theme'] = theme_name
        self.config_manager.settings.setValue('theme', theme_name)
        self.ui_setup.apply_current_theme()
        logger.info(f"Theme updated to '{theme_name}'.")

    def closeEvent(self, event) -> None:
        """Handle application close event."""
        try:
            self._save_application_state()
            self._cleanup_resources()
        except Exception as e:
            logger.error(f"Error during application close: {e}")
        event.accept()

    def _save_application_state(self) -> None:
        """Save application state before closing."""
        self.config['window_size'] = QSize(self.width(), self.height())
        self.config_manager.save_config()
        logger.info("Application settings saved.")

    def _cleanup_resources(self) -> None:
        """Clean up application resources."""
        if hasattr(self, 'page_manager'):
            self.page_manager.cleanup()


class ApplicationManager:
    """Manages the application lifecycle and initialization."""

    @staticmethod
    def initialize_logger() -> None:
        """Initialize application logging."""
        try:
            setup_logger()
            logger.info("Starting application...")
        except Exception as e:
            raise LoggerInitializationError(f"Failed to initialize logger: {str(e)}")

    @staticmethod
    def initialize_themes() -> None:
        """Initialize application themes."""
        try:
            ThemeManager.load_themes()
            logger.info("Themes loaded successfully.")
        except Exception as e:
            raise ThemeInitializationError(f"Failed to load themes: {str(e)}")

    @staticmethod
    def create_application() -> QApplication:
        """Create and configure the Qt application."""
        app = QApplication(sys.argv)
        app.text_widgets = []  # Initialize list for code block styling
        qInstallMessageHandler(qt_message_handler)
        logger.info("Qt message handler installed.")
        return app

    @classmethod
    def run_application(cls) -> NoReturn:
        """Run the application with proper error handling."""
        try:
            cls.initialize_logger()
            cls.initialize_themes()
            app = cls.create_application()

            window = MainWindow()
            window.show()
            logger.info("Application window displayed. Entering event loop.")
            ic("Application started")

            return_code = app.exec()
            logger.info(f"Application exiting with code {return_code}")
            sys.exit(return_code)

        except (LoggerInitializationError, ThemeInitializationError) as e:
            cls._handle_startup_error(str(e))
        except Exception as e:
            cls._handle_critical_error(str(e))

    @staticmethod
    def _handle_startup_error(error_message: str) -> NoReturn:
        """Handle errors during application startup."""
        logger.error(f"Startup error: {error_message}")
        QMessageBox.critical(None, "Startup Error", error_message)
        sys.exit(1)

    @staticmethod
    def _handle_critical_error(error_message: str) -> NoReturn:
        """Handle critical application errors."""
        logger.critical(f"Critical error: {error_message}")
        msg_box = QMessageBox(QMessageBox.Critical, 
                            "Critical Error",
                            "Failed to start application")
        msg_box.setDetailedText(error_message)
        msg_box.exec()
        sys.exit(1)


class ComponentInitializationError(Exception):
    """Raised when component initialization fails."""
    pass


class ApplicationSetupError(Exception):
    """Raised when application setup fails."""
    pass


class LoggerInitializationError(Exception):
    """Raised when logger initialization fails."""
    pass


class ThemeInitializationError(Exception):
    """Raised when theme initialization fails."""
    pass


if __name__ == "__main__":
    ApplicationManager.run_application()
else:
    logger.warning("This module is not meant to be imported. It should be run as the main script.")
