from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox
from Utils.Enums.enums import ThemeColors
from frontend.Theme.fonts import Fonts  # We'll create this in the theme module later

class ThemeComboBox(QComboBox):
    """Custom styled combo box for theme selections"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(Fonts.get_default(9))
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QComboBox {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                padding: 5px;
                border-radius: 4px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: url(resources/arrow-down.png);
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                selection-background-color: {ThemeColors.PRIMARY_BUTTONS.value};
            }}
        """)
