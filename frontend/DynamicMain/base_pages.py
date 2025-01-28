# ./dynamic_main/base_pages.py


from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QListWidget, QVBoxLayout, QHBoxLayout, 
    QScrollArea, QTabWidget, QStackedWidget, QSplitter,
    QLabel, QPushButton, QTextEdit
)
from Styles.theme_manager import ThemeManager
from log.logger import logger
from Config.AppConfig.config import *
from Config import ICONS
import os
from Utils.loader import load_module, get_subdirectories

class BaseModule(QWidget):
    """Abstrakt bas-klass för alla moduler med grundläggande funktionalitet."""
    module_ready = Signal()
    module_error = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.config = self.parent.config if hasattr(self.parent, 'config') else {}
        self.logger = logger
        self.theme = self.parent.config.get('theme', DEFAULT_THEME) if hasattr(self.parent, 'config') else {}
        
        self._is_initialized = False
        self._error_state = False
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        
        try:
            self.init_module()

            self._is_initialized = True
            self.module_ready.emit()
            self.logger.debug(f"Module '{self.__class__.__name__}' initialized successfully.")
        except Exception as e:
            self._error_state = True
            error_msg = f"Error initializing module {self.__class__.__name__}: {str(e)}"
            self.logger.error(error_msg)
            self.module_error.emit(str(e))
            self.display_error(error_msg)
        
    @abstractmethod
    def init_module(self):
        """Initiera modulen - måste implementeras i underklasser."""
        pass

    def on_load(self):
        """Anropas när modulen blir aktiv."""
        pass

    def on_unload(self):
        """Anropas när modulen blir inaktiv."""
        pass

    def update_theme(self, theme: dict):
        """Uppdatera temana för modulen."""
        try:
            ThemeManager.apply_widget_theme(self, theme)
            self.logger.debug(f"Theme updated for module '{self.__class__.__name__}'.")
        except Exception as e:
            self.logger.error(f"Error applying theme to module {self.__class__.__name__}: {str(e)}")

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized and not self._error_state

    def safe_cleanup(self):
        """Säker rensning av modulens resurser."""
        try:
            self.on_unload()
            self.logger.debug(f"Module '{self.__class__.__name__}' unloaded successfully.")
        except Exception as e:
            self.logger.error(f"Error during module cleanup {self.__class__.__name__}: {str(e)}")

    def display_error(self, message: str):
        """Visa ett felmeddelande i UI."""
        if hasattr(self.parent, 'error_handler'):
            self.parent.error_handler.show_error_message("Module Error", message)
        else:
            # Fallback om error_handler inte finns
            self.logger.error(message)

class BasePage(QWidget):
    """Abstrakt bas-klass för alla sidor med modulstöd."""
    page_ready = Signal()
    page_error = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.config = self.parent.config if hasattr(self.parent, 'config') else {}
        self.logger = logger
        self.theme = self.parent.config.get('theme', DEFAULT_THEME) if hasattr(self.parent, 'config') else {}
        
        self.modules: Dict[str, BaseModule] = {}
        self.current_module: Optional[str] = None
        self._error_state = False
        
        # Setup bas-layout
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        
        try:
            self.init_ui()

            self.page_ready.emit()
            self.logger.debug(f"Page '{self.__class__.__name__}' initialized successfully.")
        except Exception as e:
            self._error_state = True
            error_msg = f"Error initializing page {self.__class__.__name__}: {str(e)}"
            self.logger.error(error_msg)
            self.page_error.emit(str(e))
            self.display_error(error_msg)

    def load_frames(self):
        """Ladda QFrame komponenter automatiskt från QFrames mappen."""
        components_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'Pages', 'desktop', 'Layout', 'Page1', 'Components', 'QFrames')
        # Anpassa sökvägen beroende på layout (desktop/android)

        if self.parent.config['enable_phone_layout']:
            components_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'Pages', 'android', 'Layout', 'Page1', 'Components', 'QFrames')

        if os.path.isdir(components_dir):
            for frame_name in ['Header', 'Content', 'Footer']:
                frame_path = os.path.join(components_dir, frame_name, 'frame.py')
                if os.path.exists(frame_path):
                    module_path = f"Pages.desktop.Layout.Page1.Components.QFrames.{frame_name}.frame" if not self.parent.config['enable_phone_layout'] else f"Pages.android.Layout.Page1.Components.QFrames.{frame_name}.frame"
                    frame_module = load_module(module_path)
                    if frame_module and hasattr(frame_module, 'Frame'):
                        frame_instance = frame_module.Frame(self)
                        self.layout.addWidget(frame_instance)
                        logger.debug(f"{frame_name} QFrame loaded and added to page.")
        else:
            logger.warning(f"QFrames directory '{components_dir}' does not exist.")

    def load_widgets(self):
        """Ladda QWidget komponenter automatiskt från Widgets mappen."""
        widgets_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'Pages', 'desktop', 'Layout', 'Page1', 'Components', 'Widgets')
        # Anpassa sökvägen beroende på layout (desktop/android)

        if self.parent.config['enable_phone_layout']:
            widgets_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'Pages', 'android', 'Layout', 'Page1', 'Components', 'Widgets')

        if os.path.isdir(widgets_dir):
            for widget_name in ['Header', 'Content', 'Footer']:
                widget_path = os.path.join(widgets_dir, widget_name, 'widget.py')
                if os.path.exists(widget_path):
                    module_path = f"Pages.desktop.Layout.Page1.Components.Widgets.{widget_name}.widget" if not self.parent.config['enable_phone_layout'] else f"Pages.android.Layout.Page1.Components.Widgets.{widget_name}.widget"
                    widget_module = load_module(module_path)
                    if widget_module and hasattr(widget_module, 'Widget'):
                        widget_instance = widget_module.Widget(self)
                        self.layout.addWidget(widget_instance)
                        logger.debug(f"{widget_name} QWidget loaded and added to page.")
        else:
            logger.warning(f"Widgets directory '{widgets_dir}' does not exist.")

    @abstractmethod
    def init_ui(self):
        """Initiera UI - måste implementeras i underklasser."""
        self.load_frames()
        self.load_widgets()

    def add_module(self, name: str, module: BaseModule) -> bool:
        """Lägg till en modul till sidan."""
        try:
            if name in self.modules:
                raise ValueError(f"Module '{name}' already exists")
            
            self.modules[name] = module
            self.register_module_ui(name, module)
            self.logger.debug(f"Module '{name}' added to page '{self.__class__.__name__}'.")
            return True
        except Exception as e:
            error_msg = f"Error adding module '{name}': {str(e)}"
            self.logger.error(error_msg)
            self.display_error(error_msg)
            return False



    def register_module_ui(self, name: str, module: BaseModule):
        """Registrera modulens UI baserat på sidans layouttyp."""
        if isinstance(self, TabModulePage):
            self.tab_widget.addTab(module, name)
        elif isinstance(self, SplitModulePage):
            self.splitter.addWidget(module)
        elif isinstance(self, StackedModulePage):
            self.stacked_widget.addWidget(module)
        else:
            # Default tillagd direkt i layouten
            self.layout.addWidget(module)

    def remove_module(self, name: str) -> bool:
        """Ta bort en modul säkert."""
        try:
            if name in self.modules:
                module = self.modules[name]
                module.safe_cleanup()
                module.setParent(None)
                del self.modules[name]
                self.logger.debug(f"Module '{name}' removed from page '{self.__class__.__name__}'.")
                return True
            else:
                raise KeyError(f"Module '{name}' does not exist")
        except Exception as e:
            error_msg = f"Error removing module '{name}': {str(e)}"
            self.logger.error(error_msg)
            self.display_error(error_msg)
            return False

    def on_load(self):
        """Anropas när sidan laddas."""
        try:
            for name, module in self.modules.items():
                if module.is_initialized:
                    module.on_load()
            self.logger.debug(f"Page '{self.__class__.__name__}' loaded.")
        except Exception as e:
            error_msg = f"Error during page load {self.__class__.__name__}: {str(e)}"
            self.logger.error(error_msg)
            self.page_error.emit(str(e))

    def on_unload(self):
        """Anropas när sidan avlastas."""
        try:
            for name, module in self.modules.items():
                if module.is_initialized:
                    module.on_unload()
            self.logger.debug(f"Page '{self.__class__.__name__}' unloaded.")
        except Exception as e:
            error_msg = f"Error during page unload {self.__class__.__name__}: {str(e)}"
            self.logger.error(error_msg)
            self.page_error.emit(str(e))

    def update_theme(self, theme: dict):
        """Uppdatera temat för sidan och alla moduler."""
        try:
            ThemeManager.apply_widget_theme(self, theme)
            for module in self.modules.values():
                if module.is_initialized:
                    module.update_theme(theme)
            self.logger.debug(f"Theme updated for page '{self.__class__.__name__}'.")
        except Exception as e:
            error_msg = f"Error updating theme for page '{self.__class__.__name__}': {str(e)}"
            self.logger.error(error_msg)
            self.display_error(error_msg)

    @property
    def is_initialized(self) -> bool:
        return not self._error_state

    def display_error(self, message: str):
        """Visa ett felmeddelande i UI."""
        if hasattr(self.parent, 'error_handler'):
            self.parent.error_handler.show_error_message("Page Error", message)
        else:
            # Fallback om error_handler inte finns
            self.logger.error(message)

class ListModule(BaseModule):
    """Modul för listbaserade gränssnitt."""
    def init_module(self):
        try:
            self.list_widget = QListWidget()
            self.layout.addWidget(self.list_widget)
            self.logger.debug("ListModule initialized with QListWidget.")
        except Exception as e:
            self.logger.error(f"Error initializing ListModule: {str(e)}")
            raise
        
    def add_items(self, items: List[str]):
        """Lägg till objekt i listan."""
        try:
            self.list_widget.addItems(items)
            self.logger.debug(f"Added {len(items)} items to ListModule.")
        except Exception as e:
            self.logger.error(f"Error adding items to ListModule: {str(e)}")
            
    def clear_items(self):
        """Rensa alla objekt i listan."""
        try:
            self.list_widget.clear()
            self.logger.debug("ListModule items cleared.")
        except Exception as e:
            self.logger.error(f"Error clearing items in ListModule: {str(e)}")

class EditorModule(BaseModule):
    """Modul för textredigeringsgränssnitt."""
    def init_module(self):
        try:
            self.editor = QTextEdit()
            self.layout.addWidget(self.editor)
            self.logger.debug("EditorModule initialized with QTextEdit.")
        except Exception as e:
            self.logger.error(f"Error initializing EditorModule: {str(e)}")
            raise

    def get_text(self) -> str:
        """Hämta text från redigeraren."""
        try:
            text = self.editor.toPlainText()
            self.logger.debug("Retrieved text from EditorModule.")
            return text
        except Exception as e:
            self.logger.error(f"Error retrieving text from EditorModule: {str(e)}")
            return ""

    def set_text(self, text: str):
        """Sätt text i redigeraren."""
        try:
            self.editor.setPlainText(text)
            self.logger.debug("Set text in EditorModule.")
        except Exception as e:
            self.logger.error(f"Error setting text in EditorModule: {str(e)}")

class ProcessorModule(BaseModule):
    """Modul för databehandlingsgränssnitt."""
    def init_module(self):
        try:
            self.controls_layout = QHBoxLayout()
            self.content_layout = QVBoxLayout()
            self.layout.addLayout(self.controls_layout)
            self.layout.addLayout(self.content_layout)
            self.logger.debug("ProcessorModule initialized with QHBoxLayout and QVBoxLayout.")
        except Exception as e:
            self.logger.error(f"Error initializing ProcessorModule: {str(e)}")
            raise

class ViewerModule(BaseModule):
    """Modul för visning av innehåll."""
    def init_module(self):
        try:
            self.scroll = QScrollArea()
            self.scroll.setWidgetResizable(True)
            self.content = QWidget()
            self.content_layout = QVBoxLayout(self.content)
            self.scroll.setWidget(self.content)
            self.layout.addWidget(self.scroll)
            self.logger.debug("ViewerModule initialized with QScrollArea and QVBoxLayout.")
        except Exception as e:
            self.logger.error(f"Error initializing ViewerModule: {str(e)}")
            raise

class TabModulePage(BasePage):
    """Sida som visar moduler i flikar."""
    def init_ui(self):
        try:
            self.tab_widget = QTabWidget()
            self.layout.addWidget(self.tab_widget)
            self.logger.debug("TabModulePage initialized with QTabWidget.")
        except Exception as e:
            self.logger.error(f"Error initializing TabModulePage: {str(e)}")
            raise
        
    def add_module(self, name: str, module: BaseModule):
        if super().add_module(name, module):
            self.tab_widget.addTab(module, name)
            self.logger.debug(f"Module '{name}' added as a tab in TabModulePage.")
            return True
        return False

class SplitModulePage(BasePage):
    """Sida som visar moduler i split-view."""
    def init_ui(self):
        try:
            self.splitter = QSplitter(Qt.Horizontal)
            self.layout.addWidget(self.splitter)
            self.logger.debug("SplitModulePage initialized with QSplitter.")
        except Exception as e:
            self.logger.error(f"Error initializing SplitModulePage: {str(e)}")
            raise
        
    def add_module(self, name: str, module: BaseModule):
        if super().add_module(name, module):
            self.splitter.addWidget(module)
            self.logger.debug(f"Module '{name}' added to SplitModulePage splitter.")
            return True
        return False

class StackedModulePage(BasePage):
    """Sida som visar en modul i taget med QStackedWidget."""
    def init_ui(self):
        try:
            self.stacked_widget = QStackedWidget()
            self.layout.addWidget(self.stacked_widget)
            self.logger.debug("StackedModulePage initialized with QStackedWidget.")
        except Exception as e:
            self.logger.error(f"Error initializing StackedModulePage: {str(e)}")
            raise
        
    def add_module(self, name: str, module: BaseModule):
        if super().add_module(name, module):
            self.stacked_widget.addWidget(module)
            self.logger.debug(f"Module '{name}' added to StackedModulePage stacked widget.")
            return True
        return False
        
    def show_module(self, name: str) -> bool:
        """Växla till en specifik modul."""
        try:
            if name in self.modules:
                self.stacked_widget.setCurrentWidget(self.modules[name])
                self.logger.debug(f"Switched to module '{name}' in StackedModulePage.")
                return True
            else:
                raise KeyError(f"Module '{name}' not found in StackedModulePage.")
        except Exception as e:
            error_msg = f"Error showing module '{name}': {str(e)}"
            self.logger.error(error_msg)
            self.display_error(error_msg)
            return False

# Exportera alla klasser
__all__ = [
    'BaseModule',
    'BasePage',
    'ListModule',
    'EditorModule',
    'ProcessorModule',
    'ViewerModule',
    'TabModulePage',
    'SplitModulePage',
    'StackedModulePage'
]
