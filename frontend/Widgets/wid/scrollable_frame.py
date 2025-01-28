from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QScrollArea, QWidget, QCheckBox
from Utils.Enums.enums import ThemeColors
from frontend.Theme.fonts import Fonts  # We'll create this in the theme module later

class ScrollableFrame(QFrame):
    """Scrollable frame with switches"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Scroll Area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Content Widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add switches
        self.switches = []
        for i in range(100):
            switch = QCheckBox(f"Switch {i}")
            switch.setFont(Fonts.get_default(10))
            self.content_layout.addWidget(switch)
            self.switches.append(switch)
            
            if i in (0, 4):  # Select switches 0 and 4
                switch.setChecked(True)
        
        self.scroll_area.setWidget(self.content_widget)
        self.layout.addWidget(self.scroll_area)
        
        # Styling
        self.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {ThemeColors.PRIMARY.value};
            }}
            QCheckBox {{
                color: {ThemeColors.TEXT_PRIMARY.value};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {ThemeColors.TERTIARY.value};
                border-radius: 4px;
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
            }}
            QCheckBox::indicator:checked {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
                border-color: {ThemeColors.PRIMARY_BUTTONS.value};
            }}
            QCheckBox::indicator:hover {{
                border-color: {ThemeColors.HOVER_BUTTONS.value};
            }}
        """)
