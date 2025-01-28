# ./_markdown_csv_extractor/components/AppearanceSection.py

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QCheckBox, QProgressBar
from PySide6.QtGui import QFont
from ..Theme import ThemeColors, AppTheme
from ..GUI_Constants_and_Settings import GuiConstants, SettingsManager
from PySide6.QtCore import (
    Qt, Signal, QObject, QTimer, QThread, Slot,
    QPoint, QPropertyAnimation, QEasingCurve
)
from PySide6.QtGui import (
    QFont, QPalette, QColor, QKeyEvent
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea, QLineEdit,
    QFileDialog, QMessageBox, QCheckBox, QProgressBar,
    QListWidget, QSizePolicy, QInputDialog, QComboBox, QSplitter, QScrollerProperties, QScroller
)

class AppearanceSection(QFrame):
    """Section for appearance settings"""
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header
        header = QLabel("Appearance Settings")
        header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(header)

        # Dark mode toggle
        self.dark_mode_toggle = QCheckBox("Enable Dark Mode")
        is_dark_mode = self.settings_manager.get_setting("appearance", "dark_mode", True)
        self.dark_mode_toggle.setChecked(is_dark_mode)
        self.dark_mode_toggle.toggled.connect(self.toggle_dark_mode)
        layout.addWidget(self.dark_mode_toggle)

        # UI scaling
        scaling_label = QLabel("UI Scaling")
        self.scaling_bar = QProgressBar()
        self.scaling_bar.setMinimum(50)
        self.scaling_bar.setMaximum(150)
        self.scaling_bar.setValue(self.settings_manager.get_setting("appearance", "ui_scaling", 100))
        self.scaling_bar.setFormat("%v%")
        self.scaling_bar.setTextVisible(True)
        self.scaling_bar.valueChanged.connect(self.update_ui_scaling)

        layout.addWidget(scaling_label)
        layout.addWidget(self.scaling_bar)

    def toggle_dark_mode(self, enabled: bool):
        """Enable or disable dark mode"""
        self.settings_manager.update_setting("appearance", "dark_mode", enabled)
        print(f"AppearanceSection: Dark mode {'enabled' if enabled else 'disabled'}")  # Debug
        ThemeColors.set_theme(enabled)
        AppTheme.apply_theme(QApplication.instance())

    def update_ui_scaling(self, value: int):
        """Update UI scaling"""
        self.settings_manager.update_setting("appearance", "ui_scaling", value)
        scaling_factor = value / 100.0
        font = QApplication.instance().font()
        font.setPointSize(max(int(10 * scaling_factor), 8))  # Ensure font size doesn't go below 8
        QApplication.instance().setFont(font)
        print(f"AppearanceSection: UI scaling set to {value}%")  # Debug
