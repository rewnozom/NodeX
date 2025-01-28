from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSlider
from Utils.Enums.enums import ThemeColors

class CustomSlider(QSlider):
    """Enhanced slider with custom styling"""
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 6px;
                background: {ThemeColors.SECONDARY_BACKGROUND.value};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {ThemeColors.PRIMARY_BUTTONS.value};
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QSlider::groove:vertical {{
                width: 6px;
                background: {ThemeColors.SECONDARY_BACKGROUND.value};
                border-radius: 3px;
            }}
            QSlider::handle:vertical {{
                background: {ThemeColors.PRIMARY_BUTTONS.value};
                height: 18px;
                margin: 0 -6px;
                border-radius: 9px;
            }}
        """)
