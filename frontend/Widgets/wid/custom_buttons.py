from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from Utils.Enums.enums import ThemeColors
from frontend.Theme.fonts import Fonts  # We'll create this in the theme module later

class SidebarButton(QPushButton):
    """Custom styled sidebar button"""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFont(Fonts.get_default(10))
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.PRIMARY.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                padding: 10px;
                text-align: left;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
            }}
            QPushButton:disabled {{
                background-color: {ThemeColors.PRIMARY.value};
                color: #666666;
                border: 1px solid #333333;
            }}
        """)

class SegmentedButton(QPushButton):
    """Custom segmented button implementation"""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setFont(Fonts.get_default(10))
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                padding: 8px 16px;
            }}
            QPushButton:checked {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.HOVER_BUTTONS.value};
            }}
        """)

class CustomButton(QPushButton):
    """Custom styled button for the radio frame"""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFont(Fonts.get_default(10))
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                padding: 10px 20px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.HOVER_BUTTONS.value};
            }}
            QPushButton:pressed {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
            }}
        """)
