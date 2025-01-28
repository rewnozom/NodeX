# pages/base_page.py

from PySide6.QtWidgets import QWidget, QVBoxLayout

class Page(QWidget):
    """Base Page class to provide a consistent layout for derived pages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        """Initialize the UI layout for the page."""
        layout = QVBoxLayout(self)
        self.setLayout(layout)
