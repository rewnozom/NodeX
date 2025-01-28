from PySide6.QtCore import Qt
from PySide6.QtWidgets import QProgressBar
from Utils.Enums.enums import ThemeColors

class CustomProgressBar(QProgressBar):
    """Enhanced progress bar with custom styling"""
    def __init__(self, parent=None, orientation=Qt.Horizontal):
        super().__init__(parent)
        self.setOrientation(orientation)
        self.setStyleSheet(f"""
            QProgressBar {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 3px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
                border-radius: 2px;
            }}
        """)
