# ..\theme_manager.py
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

def apply_dark_orange_theme(app):
    # Basfärger
    primary_bg = QColor(43, 41, 41, int(0.85 * 255))
    secondary_bg = QColor(66, 63, 63)
    
    # Textfärger
    primary_text = QColor(199, 194, 194)
    secondary_text = QColor("#a3a3a3")
    
    # Accentfärger
    primary_accent = QColor(240, 133, 46)
    secondary_accent = QColor(226, 107, 21, int(0.88 * 255))
    tertiary_accent = QColor(223, 87, 13, int(0.88 * 255))
    
    # Specialeffekter
    border_color = QColor(82, 82, 82, int(0.3 * 255))
    glass_bg = QColor(26, 26, 26, int(0.9 * 255))
    
    # Create palette for dark mode
    palette = QPalette()
    palette.setColor(QPalette.Window, primary_bg)
    palette.setColor(QPalette.WindowText, primary_text)
    palette.setColor(QPalette.Base, secondary_bg)
    palette.setColor(QPalette.AlternateBase, primary_bg)
    palette.setColor(QPalette.ToolTipBase, primary_text)
    palette.setColor(QPalette.ToolTipText, primary_text)
    palette.setColor(QPalette.Text, primary_text)
    palette.setColor(QPalette.Button, secondary_bg)
    palette.setColor(QPalette.ButtonText, primary_text)
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Highlight, primary_accent)
    palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)
    
    # Set application stylesheet
    stylesheet = f"""
        QWidget {{
            background-color: rgba({primary_bg.red()}, {primary_bg.green()}, {primary_bg.blue()}, {primary_bg.alpha()});
            color: rgb({primary_text.red()}, {primary_text.green()}, {primary_text.blue()});
            border: 1px solid rgba({border_color.red()}, {border_color.green()}, {border_color.blue()}, {border_color.alpha()});
            border-radius: 5px;
        }}
        QGroupBox {{
            border: 1px solid rgba({border_color.red()}, {border_color.green()}, {border_color.blue()}, {border_color.alpha()});
            margin-top: 10px;
            border-radius: 5px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 3px;
            color: rgb({primary_accent.red()}, {primary_accent.green()}, {primary_accent.blue()});
        }}
        QPushButton {{
            background-color: rgba({secondary_bg.red()}, {secondary_bg.green()}, {secondary_bg.blue()}, 255);
            border: none;
            padding: 5px;
            border-radius: 5px;
        }}
        QPushButton:hover {{
            background-color: rgba({primary_accent.red()}, {primary_accent.green()}, {primary_accent.blue()}, 200);
        }}
        QLineEdit, QTextEdit {{
            background-color: rgba({glass_bg.red()}, {glass_bg.green()}, {glass_bg.blue()}, {glass_bg.alpha()});
            border: 1px solid rgba({border_color.red()}, {border_color.green()}, {border_color.blue()}, {border_color.alpha()});
            border-radius: 5px;
            padding: 5px;
        }}
        QTabWidget::pane {{
            border: 1px solid rgba({border_color.red()}, {border_color.green()}, {border_color.blue()}, {border_color.alpha()});
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }}
        QTabBar::tab {{
            background: rgba({secondary_bg.red()}, {secondary_bg.green()}, {secondary_bg.blue()}, 255);
            color: rgb({primary_text.red()}, {primary_text.green()}, {primary_text.blue()});
            padding: 10px;
            margin: 2px;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }}
        QTabBar::tab:selected {{
            background: rgb({primary_accent.red()}, {primary_accent.green()}, {primary_accent.blue()});
            color: rgb(0, 0, 0);
        }}
    """
    app.setStyleSheet(stylesheet)
