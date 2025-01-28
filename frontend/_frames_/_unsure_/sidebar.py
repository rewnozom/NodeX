from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSpacerItem, QSizePolicy
from frontend.Theme.fonts import Fonts
from ui.widgets.custom_buttons import SidebarButton
from ui.widgets.theme_combo_box import ThemeComboBox
from Utils.Enums.enums import ThemeColors
# Now copy the SidebarFrame class from gui.py here

class SidebarFrame(QFrame):
    # Signals for theme and scaling changes
    appearance_mode_changed = Signal(str)
    scaling_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarFrame")
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Initialize and setup the UI components"""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 20, 10, 20)
        self.layout.setSpacing(10)
        
        # Logo/Title
        self.logo_label = QLabel("Tobias.R")
        self.logo_label.setFont(Fonts.get_bold(20))
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.logo_label)
        
        # Sidebar buttons
        self.buttons = []
        for i in range(3):
            btn = SidebarButton(f"Button {i+1}")
            btn.clicked.connect(lambda checked, idx=i: self.sidebar_button_event(idx))
            self.buttons.append(btn)
            self.layout.addWidget(btn)
        
        # Disable third button
        self.buttons[2].setEnabled(False)
        self.buttons[2].setText("Disabled Button")
        
        # Add vertical spacer
        self.layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        
        # Appearance mode section
        self.appearance_label = QLabel("Appearance Mode:")
        self.appearance_label.setFont(Fonts.get_default(9))
        self.layout.addWidget(self.appearance_label)
        
        self.appearance_mode_combo = ThemeComboBox()
        self.appearance_mode_combo.addItems(["Light", "Dark", "System"])
        self.appearance_mode_combo.setCurrentText("Dark")
        self.layout.addWidget(self.appearance_mode_combo)
        
        # UI Scaling section
        self.scaling_label = QLabel("UI Scaling:")
        self.scaling_label.setFont(Fonts.get_default(9))
        self.layout.addWidget(self.scaling_label)
        
        self.scaling_combo = ThemeComboBox()
        self.scaling_combo.addItems(["80%", "90%", "100%", "110%", "120%"])
        self.scaling_combo.setCurrentText("100%")
        self.layout.addWidget(self.scaling_combo)
        
        # Set fixed width for sidebar
        self.setFixedWidth(200)
        
        # Apply frame styling
        self.setStyleSheet(f"""
            QFrame#sidebarFrame {{
                background-color: {ThemeColors.PRIMARY.value};
                border-right: 1px solid {ThemeColors.TERTIARY.value};
            }}
            QLabel {{
                color: {ThemeColors.TEXT_PRIMARY.value};
            }}
        """)

    def setup_connections(self):
        """Setup signal connections"""
        self.appearance_mode_combo.currentTextChanged.connect(
            self.change_appearance_mode_event
        )
        self.scaling_combo.currentTextChanged.connect(
            self.change_scaling_event
        )

    def sidebar_button_event(self, button_index: int):
        """Handle sidebar button clicks"""
        print(f"Sidebar button {button_index + 1} clicked")
        # Emit custom signal or handle the event as needed

    def change_appearance_mode_event(self, new_appearance_mode: str):
        """Handle appearance mode changes"""
        self.appearance_mode_changed.emit(new_appearance_mode)
        # You might want to update the theme here
        
    def change_scaling_event(self, new_scaling: str):
        """Handle UI scaling changes"""
        try:
            scaling_float = float(new_scaling.replace("%", "")) / 100
            self.scaling_changed.emit(str(scaling_float))
            # Implement the actual scaling logic here
        except ValueError:
            print(f"Invalid scaling value: {new_scaling}")

    def add_custom_button(self, text: str, callback) -> SidebarButton:
        """Add a new custom button to the sidebar"""
        btn = SidebarButton(text)
        btn.clicked.connect(callback)
        # Insert before the spacer
        self.layout.insertWidget(len(self.buttons), btn)
        self.buttons.append(btn)
        return btn

    def remove_button(self, button: SidebarButton):
        """Remove a button from the sidebar"""
        if button in self.buttons:
            self.buttons.remove(button)
            self.layout.removeWidget(button)
            button.deleteLater()
