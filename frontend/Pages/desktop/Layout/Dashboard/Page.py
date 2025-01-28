from frontend.DynamicMain.base_pages import BasePage
from PySide6.QtWidgets import QWidget, QVBoxLayout
from . import dashboard

class IsolatedDashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.dashboard = dashboard.Dashboard()
        # Remove frameless window flags for integration
        self.dashboard.setWindowFlags(self.dashboard.windowFlags() & ~dashboard.Qt.FramelessWindowHint)
        self.dashboard.title_bar.hide()  # Hide custom title bar
        self.layout.addWidget(self.dashboard)

class Page(BasePage):
    def init_ui(self):
        super().init_ui()
        self.isolated_widget = IsolatedDashboardWidget()
        self.layout.addWidget(self.isolated_widget)
    
    def on_unload(self):
        super().on_unload()
        if hasattr(self.isolated_widget, 'dashboard'):
            self.isolated_widget.dashboard.close()