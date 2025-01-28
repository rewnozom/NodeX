# ./frontend/Pages/desktop/Layout/Markdown_CSV_Extr/Page.py

from frontend.DynamicMain.base_pages import BasePage
from . import gui
from PySide6.QtWidgets import QWidget

class IsolatedAppWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = gui.QVBoxLayout(self)
        self.app = gui.App()
        self.app.setParent(None)  # Detach from parent widget hierarchy
        self.layout.addWidget(self.app)

class Page(BasePage):
    def init_ui(self):
        super().init_ui()
        self.isolated_widget = IsolatedAppWidget()
        self.layout.addWidget(self.isolated_widget)
    
    def on_load(self):
        super().on_load()
        if hasattr(self.isolated_widget, 'app'):
            gui.QTimer.singleShot(0, self.isolated_widget.app.setup_ui)
            gui.QTimer.singleShot(100, self.isolated_widget.app.setup_connections)

    def on_unload(self):
        super().on_unload()
        if hasattr(self.isolated_widget, 'app'):
            self.isolated_widget.app.closeEvent(gui.QEvent(gui.QEvent.Type.Close))