# ./_markdown_csv_extractor/Theme.py

from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication

class ThemeColors:
    PRIMARY = "#18181B"      # zinc-900
    SECONDARY = "#27272A"    # zinc-800
    ACCENT = "#EF4444"       # red-500
    ACCENT_HOVER = "#DC2626" # red-600
    TEXT = "#FFFFFF"
    BORDER = "#3F3F46"       # zinc-700
    DISABLED = "#52525B"     # zinc-600

    @classmethod
    def set_theme(cls, is_dark: bool):
        if is_dark:
            cls.PRIMARY = "#18181B"      # dark theme
            cls.SECONDARY = "#27272A"
            cls.TEXT = "#FFFFFF"
        else:
            cls.PRIMARY = "#FFFFFF"      # light theme
            cls.SECONDARY = "#F4F4F5"
            cls.TEXT = "#000000"

class AppTheme:
    @staticmethod
    def get_base_stylesheet():
        return f"""
            QWidget {{
                background-color: {ThemeColors.PRIMARY};
                color: {ThemeColors.TEXT};
                font-family: 'Segoe UI', sans-serif;
            }}
            
            QPushButton {{
                background-color: {ThemeColors.ACCENT};
                border: none;
                padding: 12px;
                border-radius: 4px;
                color: {ThemeColors.TEXT};
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {ThemeColors.ACCENT_HOVER};
            }}
            
            QPushButton:disabled {{
                background-color: {ThemeColors.DISABLED};
            }}
            
            QLineEdit {{
                background-color: {ThemeColors.SECONDARY};
                border: 1px solid {ThemeColors.BORDER};
                padding: 8px;
                border-radius: 4px;
            }}
            
            QProgressBar {{
                border: none;
                background-color: {ThemeColors.SECONDARY};
                border-radius: 2px;
                height: 8px;
            }}
            
            QProgressBar::chunk {{
                background-color: {ThemeColors.ACCENT};
                border-radius: 2px;
            }}
            
            QScrollArea {{
                border: none;
            }}
            
            QListWidget {{
                background-color: {ThemeColors.SECONDARY};
                border: 1px solid {ThemeColors.BORDER};
                border-radius: 4px;
                padding: 4px;
                height: 200px;  /* Adjusted height for multiple rows */
            }}
            
            QListWidget::item {{
                padding: 8px;
                border-radius: 2px;
            }}
            
            QListWidget::item:hover {{
                background-color: {ThemeColors.BORDER};
            }}
        """

    @staticmethod
    def apply_theme(app: QApplication):
        app.setStyle("Fusion")
        app.setStyleSheet(AppTheme.get_base_stylesheet())
        
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(ThemeColors.PRIMARY))
        palette.setColor(QPalette.WindowText, QColor(ThemeColors.TEXT))
        palette.setColor(QPalette.Base, QColor(ThemeColors.SECONDARY))
        palette.setColor(QPalette.Text, QColor(ThemeColors.TEXT))
        palette.setColor(QPalette.Button, QColor(ThemeColors.ACCENT))
        palette.setColor(QPalette.ButtonText, QColor(ThemeColors.TEXT))
        palette.setColor(QPalette.Link, QColor(ThemeColors.ACCENT))
        palette.setColor(QPalette.Highlight, QColor(ThemeColors.ACCENT_HOVER))
        palette.setColor(QPalette.HighlightedText, QColor(ThemeColors.TEXT))
        app.setPalette(palette)
