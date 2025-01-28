# ./frontend/Pages/desktop/Layout/Markdown_CSV_Extr/

from frontend.DynamicMain.base_pages import BasePage
from gui import *

class Page(BasePage):
    def init_ui(self):
        super().init_ui()
        self.app = App()
        self.layout.addWidget(self.app)
    
    def on_load(self):
        super().on_load()
        if hasattr(self, 'app'):
            QTimer.singleShot(0, self.app.setup_ui)
            QTimer.singleShot(100, self.app.setup_connections)
            QTimer.singleShot(200, lambda: AppTheme.apply_theme(QApplication.instance()))

    def on_unload(self):
        super().on_unload()
        if hasattr(self, 'app'):
            self.app.closeEvent(QEvent(QEvent.Type.Close))