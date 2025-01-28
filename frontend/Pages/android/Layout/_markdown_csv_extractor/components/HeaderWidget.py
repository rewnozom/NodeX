# ./_markdown_csv_extractor/components/HeaderWidget.py

from PySide6.QtCore import (
    Qt, Signal, QObject, QTimer, QThread, Slot,
    QPoint, QPropertyAnimation, QEasingCurve
)
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtGui import QFont
from ..Theme import ThemeColors

class HeaderWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Menu button
        self.menu_btn = QPushButton("☰")
        self.menu_btn.setFixedSize(32, 32)
        self.menu_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.SECONDARY};
                border-radius: 4px;
                font-size: 18px;
            }}
        """)
        
        # Title
        self.title = QLabel("Extraction Tool")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        # Settings button
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.SECONDARY};
                border-radius: 4px;
                font-size: 18px;
            }}
        """)
        
        layout.addWidget(self.menu_btn)
        layout.addWidget(self.title, 1, Qt.AlignCenter)
        layout.addWidget(self.settings_btn)
