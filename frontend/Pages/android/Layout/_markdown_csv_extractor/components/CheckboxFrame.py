# ./_markdown_csv_extractor/components/CheckboxFrame.py

from PySide6.QtWidgets import QFrame, QVBoxLayout, QCheckBox, QLabel
from PySide6.QtGui import QFont
from PySide6.QtCore import (
    Qt, Signal, QObject, QTimer, QThread, Slot,
    QPoint, QPropertyAnimation, QEasingCurve
)
from ..Theme import ThemeColors

class CheckboxFrame(QFrame):
    """Frame containing extraction checkboxes"""
    extract_csv_changed = Signal(bool)
    extract_markdown_changed = Signal(bool)
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Initialize the UI components"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # CSV Checkbox
        self.checkbox_extract_csv = QCheckBox("Extract - CSV")
        self.checkbox_extract_csv.setFont(QFont("Segoe UI", 10))
        self.checkbox_extract_csv.setChecked(self.settings_manager.get_setting("extractions", "extract_csv", False))
        self.layout.addWidget(self.checkbox_extract_csv)
        
        # Markdown Checkbox
        self.checkbox_extract_markdown = QCheckBox("Extract - Markdown")
        self.checkbox_extract_markdown.setFont(QFont("Segoe UI", 10))
        self.checkbox_extract_markdown.setChecked(self.settings_manager.get_setting("extractions", "extract_markdown", False))
        self.layout.addWidget(self.checkbox_extract_markdown)
        
        # Add stretching space
        self.layout.addStretch()

    def setup_connections(self):
        self.checkbox_extract_csv.stateChanged.connect(
            lambda state: self.extract_csv_changed.emit(bool(state))
        )
        self.checkbox_extract_markdown.stateChanged.connect(
            lambda state: self.extract_markdown_changed.emit(bool(state))
        )
