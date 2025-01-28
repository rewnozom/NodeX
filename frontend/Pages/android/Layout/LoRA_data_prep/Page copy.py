from frontend.DynamicMain.base_pages import BasePage
from PySide6.QtWidgets import QWidget, QVBoxLayout
from . import lora_prep

class IsolatedLoraWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Initialize without applying global theme
        settings = lora_prep.AppSettings()
        app_logger = lora_prep.AppLogger(settings)
        self.window = lora_prep.MainWindow()
        
        # Remove window frame features
        self.window.setWindowFlags(self.window.windowFlags() & ~lora_prep.Qt.Window)
        self.layout.addWidget(self.window)

class Page(BasePage):
    def init_ui(self):
        super().init_ui()
        self.isolated_widget = IsolatedLoraWidget()
        self.layout.addWidget(self.isolated_widget)
    
    def on_unload(self):
        super().on_unload()
        if hasattr(self.isolated_widget, 'window'):
            self.isolated_widget.window.close()