# ./frontend/pages/desktop/Layout/1_new/new_page.py


from frontend.DynamicMain.base_pages import (
    BasePage, TabModulePage, SplitModulePage, StackedModulePage,
    BaseModule, ListModule, EditorModule, ProcessorModule, ViewerModule
)
from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit
from PySide6.QtCore import Qt
from log.logger import logger

# Define your custom modules by extending BaseModule or any specialized module
class CustomModule(BaseModule):
    def init_module(self):
        super().init_module()
        self.label = QLabel("Welcome to Custom Module")
        self.button = QPushButton("Click Me")
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button)
        self.button.clicked.connect(self.on_button_click)

    def on_button_click(self):
        logger.info("CustomModule: Button clicked!")
        # Additional logic here

# Optionally, define more specialized modules
class TextEditorModule(EditorModule):
    def init_module(self):
        super().init_module()
        self.editor = QTextEdit()
        self.layout.addWidget(self.editor)

    def get_text(self):
        return self.editor.toPlainText()

    def set_text(self, text):
        self.editor.setPlainText(text)

# Now, create your page by extending one of the BasePage classes
class Page(TabModulePage):  # You can also use SplitModulePage or StackedModulePage
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_modules()

    def setup_modules(self):
        # Add CustomModule to the page
        custom_module = CustomModule(self)
        self.add_module("Custom Module", custom_module)

        # Add TextEditorModule to the page
        text_editor_module = TextEditorModule(self)
        self.add_module("Text Editor", text_editor_module)

    def on_load(self):
        super().on_load()
        logger.info("Page loaded")

    def on_unload(self):
        super().on_unload()
        logger.info("Page unloaded")

    def update_theme(self, theme):
        super().update_theme(theme)
        logger.info(f"Page theme updated to {theme}")

# For a simple page without modules, you can use BasePage directly
class SimplePage(BasePage):
    def init_ui(self):
        super().init_ui()
        title = QLabel("Simple Page")
        title.setAlignment(Qt.AlignCenter)
        button = QPushButton("Click Me")
        self.layout.addWidget(title)
        self.layout.addWidget(button)
        button.clicked.connect(self.on_button_click)

    def on_button_click(self):
        logger.info("SimplePage: Button clicked!")
        # Additional logic here

    def on_load(self):
        super().on_load()
        logger.info("SimplePage loaded")

    def on_unload(self):
        super().on_unload()
        logger.info("SimplePage unloaded")