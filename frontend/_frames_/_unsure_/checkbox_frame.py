from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QCheckBox
from Utils.Enums.enums import ThemeColors
from frontend.Theme.fonts import Fonts


class CheckboxFrame(QFrame):
    """Frame containing extraction checkboxes"""
    extract_csv_changed = Signal(bool)
    extract_markdown_changed = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        
        # CSV Checkbox
        self.checkbox_extract_csv = QCheckBox("Extract - CSV")
        self.checkbox_extract_csv.setFont(Fonts.get_default(10))
        self.layout.addWidget(self.checkbox_extract_csv)
        
        # Markdown Checkbox
        self.checkbox_extract_markdown = QCheckBox("Extract - Markdown")
        self.checkbox_extract_markdown.setFont(Fonts.get_default(10))
        self.layout.addWidget(self.checkbox_extract_markdown)
        
        # Add stretching space
        self.layout.addStretch()
        
        # Styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.PRIMARY.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 4px;
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

    def setup_connections(self):
        self.checkbox_extract_csv.stateChanged.connect(
            lambda state: self.extract_csv_changed.emit(bool(state))
        )
        self.checkbox_extract_markdown.stateChanged.connect(
            lambda state: self.extract_markdown_changed.emit(bool(state))
        )

    @property
    def extract_csv(self) -> bool:
        return self.checkbox_extract_csv.isChecked()
        
    @property
    def extract_markdown(self) -> bool:
        return self.checkbox_extract_markdown.isChecked()
