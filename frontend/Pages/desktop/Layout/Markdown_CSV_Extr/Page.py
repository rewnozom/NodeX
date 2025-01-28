# ./frontend/Pages/desktop/Layout/Markdown_CSV_Extr/Page.py

from frontend.DynamicMain.base_pages import BasePage
from . import gui

class Page(BasePage):
    def init_ui(self):
        super().init_ui()
        self.app = gui.App()

        self.app.setStyleSheet("")
        self.layout.addWidget(self.app)
    
    def on_load(self):
        super().on_load()
        if hasattr(self, 'app'):
            gui.QTimer.singleShot(0, self.app.setup_ui)
            gui.QTimer.singleShot(100, self.app.setup_connections)

    def on_unload(self):
        super().on_unload()
        if hasattr(self, 'app'):
            self.app.closeEvent(gui.QEvent(gui.QEvent.Type.Close))