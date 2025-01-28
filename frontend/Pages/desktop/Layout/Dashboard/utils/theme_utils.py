# ./utils/theme_utils.py
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QLabel, QFrame, QScrollArea, QCheckBox, QInputDialog, QGridLayout,
    QGroupBox, QComboBox, QSizePolicy, QSpacerItem
)
from PySide6.QtGui import QPalette, QColor, QLinearGradient
from PySide6.QtCore import Qt

def apply_dark_theme(widget):
    """
    Apply a consistent dark theme to the given widget and its children.
    This function forces dark colors throughout by setting a dark gradient for the window
    and replacing any white backgrounds with darker shades.
    """
    # Create a dark vertical gradient for widget backgrounds.
    gradient = QLinearGradient(0, 0, 0, widget.height())
    gradient.setColorAt(0, QColor(20, 20, 20))
    gradient.setColorAt(1, QColor(40, 40, 40))
    
    # Obtain the current palette and override colors to avoid any white backgrounds.
    palette = widget.palette()
    
    # Window and dialog backgrounds
    palette.setBrush(QPalette.Window, gradient)
    palette.setColor(QPalette.WindowText, QColor(220, 220, 220))
    
    # Widget base area (e.g., QLineEdit, QTextEdit, QListWidget backgrounds)
    palette.setColor(QPalette.Base, QColor(30, 30, 30))
    palette.setColor(QPalette.AlternateBase, QColor(35, 35, 35))
    
    # Buttons and button texts
    palette.setColor(QPalette.Button, QColor(45, 45, 45))
    palette.setColor(QPalette.ButtonText, QColor(230, 230, 230))
    
    # Tooltips should also follow the dark theme
    palette.setColor(QPalette.ToolTipBase, QColor(30, 30, 30))
    palette.setColor(QPalette.ToolTipText, QColor(230, 230, 230))
    
    # Text elements across the app
    palette.setColor(QPalette.Text, QColor(230, 230, 230))
    palette.setColor(QPalette.PlaceholderText, QColor(150, 150, 150))
    
    # Selection (highlight) colors
    palette.setColor(QPalette.Highlight, QColor(70, 70, 70))
    palette.setColor(QPalette.HighlightedText, QColor(230, 230, 230))
    
    # Disabled elements (using grayish hues instead of white)
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(100, 100, 100))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(100, 100, 100))
    
    widget.setPalette(palette)
    
    # Optionally, force updating the style for child widgets by setting autoFillBackground.
    widget.setAutoFillBackground(True)
    
    # Recursively apply the dark theme to all child widgets
    for child in widget.findChildren(QWidget):
        child.setPalette(widget.palette())
        child.setAutoFillBackground(True)
