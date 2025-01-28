# ./shared/theme/theme_manager.py


import json
import os
import sys

from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QTextEdit, QTextBrowser

from .code_block_style import apply_code_block_style  # Import only the necessary function

from log.logger import logger, message_collector  # **Updated Import**

# def add_project_subdirectories_to_syspath(root_dir):
#     """
#     Recursively add all subdirectories of the project root to sys.path.
#     """
#     for dirpath, dirnames, _ in os.walk(root_dir):
#         if dirpath not in sys.path:
#             sys.path.insert(0, dirpath)

# # Automatically detect the project root (adjust the path levels if needed)
# project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# add_project_subdirectories_to_syspath(project_root)


class ThemeManager:
    current_theme = None
    current_theme_name = None
    themes = {}

    DEFAULT_THEME = {
        'TYPOGRAPHY': {
            'font_family': 'Arial',
            'body_font_size': '14px',
            'h3_font_size': '16px',
            'small_font_size': '12px'
        },
        'BASE': {
            'primary_color': '#2D2D2D',
            'secondary_color': '#383838',
            'text_color': '#FFFFFF',
            'subtext_color': '#AAAAAA'
        },
        'UI_ELEMENT': {
            'border_color': '#555555',
            'hover_color': '#444444',
            'active_color': '#666666',
            'selection_color': '#0078D7'
        },
        'MENU': {
            'menu_background_gradient_start': '#2D2D2D',
            'menu_background_gradient_end': '#383838',
            'menu_hover_background_gradient_start': '#444444',
            'menu_hover_background_gradient_end': '#4A4A4A',
            'menu_active_background_gradient_start': '#555555',
            'menu_active_background_gradient_end': '#5A5A5A',
            'menu_text_color': '#FFFFFF',
            'menu_item_padding': '8px'
        },
        'OVERLAY_AND_SHADOW': {
            'shadow_color': '#1A1A1A'
        },
        'CODE_BLOCK_STYLE': {
            'background_color': '#1E1E1E',
            'text_color': '#D4D4D4',
            'keyword_color': '#569CD6',
            'string_color': '#CE9178',
            'comment_color': '#6A9955',
            'function_color': '#DCDCAA',
            'number_color': '#B5CEA8',
            'operator_color': '#D4D4D4',
            'font_family': 'Consolas, Courier New, monospace',
            'font_size': '12px',  # Reduced base font size
            'code_font_size': '10px'  # Further reduced font size for code
        }
    }

    @staticmethod
    def load_themes(themes_directory="./Styles/theme"):
        """
        Load all theme JSON files from the specified directory.
        Each subdirectory represents a theme (e.g., dark, light).
        """
        if not os.path.isdir(themes_directory):
            logger.error(f"Themes directory not found: {themes_directory}")
            message_collector.add_message("themes_directory_missing", f"Themes directory not found: {themes_directory}")
            return

        for theme_name in os.listdir(themes_directory):
            # Skip non-theme directories like __pycache__
            if theme_name == "__pycache__" or not os.path.isdir(os.path.join(themes_directory, theme_name)):
                continue
                
            theme_dir = os.path.join(themes_directory, theme_name)
            theme_path = os.path.join(theme_dir, "style.json")
            if os.path.isfile(theme_path):
                with open(theme_path, 'r') as f:
                    try:
                        data = json.load(f)
                        ThemeManager.themes[theme_name] = data
                        logger.info(f"Loaded theme '{theme_name}' from {theme_path}")
                        message_collector.add_message("discovered_page", f"Loaded theme '{theme_name}'")
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding JSON for theme '{theme_name}': {e}")
                        message_collector.add_message("error_decoding_theme", f"Theme '{theme_name}': {str(e)}")
            else:
                logger.warning(f"No style.json found for theme '{theme_name}' in {theme_dir}")
                message_collector.add_message("missing_style_json", f"No style.json found for theme '{theme_name}'")

    @staticmethod
    def apply_theme(theme_name='dark'):
        """
        Apply the specified theme by name.
        """
        if theme_name == ThemeManager.current_theme_name:
            logger.debug(f"Theme '{theme_name}' is already applied. Skipping re-application.")
            return  # Exit early to prevent duplicate applications

        if theme_name not in ThemeManager.themes:
            logger.error(f"Theme '{theme_name}' not found in themes.")
            message_collector.add_message("theme_not_found", f"Theme '{theme_name}' not found.")
            return
        
        theme = ThemeManager.themes[theme_name]
        ThemeManager.current_theme = theme
        ThemeManager.current_theme_name = theme_name
        
        qss = ThemeManager.construct_qss(theme)
        QApplication.instance().setStyleSheet(qss)
        
        ThemeManager.apply_palette(theme)
        logger.info(f"Applied theme: {theme_name}")
        message_collector.add_message("applied_theme", f"CURRENT_THEME = {theme_name}")
        
        # Apply code block styles to all registered text widgets
        code_block_styles = theme.get('CODE_BLOCK_STYLE', {})
        ThemeManager.apply_code_block_style_to_all(code_block_styles)
    
    @staticmethod
    def construct_qss(theme):
        """
        Construct the QSS stylesheet string from the theme dictionary.
        """
        try:
            qss = ""
            for key, value in theme.items():
                if key.endswith("_style"):
                    widget_class = key.replace("_style", "")
                    qss += ThemeManager.build_widget_style(widget_class, value)
            return qss
        except Exception as e:
            logger.error(f"Error constructing QSS: {e}")
            message_collector.add_message("error_constructing_qss", f"Error constructing QSS: {str(e)}")
            return ""

    @staticmethod
    def build_widget_style(widget_class, styles):
        """
        Build QSS for a specific widget class.
        """
        qss = f"{widget_class} {{\n"
        qss += ThemeManager._build_base_style(styles)
        
        # Add explicit control for QTabWidget and QToolButton if defined in the styles
        if widget_class == 'QTabWidget':
            qss += f"    padding: {styles.get('tab_padding', '10px')};\n"
            qss += f"    background-color: {styles.get('tab_background', '#2D2D2D')};\n"
        
        if widget_class == 'QToolButton':
            qss += f"    icon-size: {styles.get('icon_size', '36px')};\n"  # Adjust size from theme file

        qss += "}\n\n"
        qss += ThemeManager._build_pseudo_states(widget_class, styles)
        qss += ThemeManager._build_subcontrols(widget_class, styles)
        return qss

    @staticmethod
    def _build_base_style(styles):
        """Build the base style for a widget."""
        base_qss = ""
        for prop, val in styles.items():
            if not isinstance(val, dict):
                css_prop = prop.replace('_', '-')
                base_qss += f"    {css_prop}: {val};\n"
            elif 'gradient' in prop.lower() and 'hover' not in prop.lower() and 'pressed' not in prop.lower():
                base_qss += ThemeManager.construct_gradient(val, 'background')
        return base_qss

    @staticmethod
    def _build_pseudo_states(widget_class, styles):
        """Build pseudo-states for a widget."""
        pseudo_states_qss = ""
        for prop, val in styles.items():
            if isinstance(val, dict) and 'gradient' in prop.lower():
                if 'hover' in prop.lower():
                    pseudo_states_qss += f"{widget_class}:hover {{\n"
                    pseudo_states_qss += ThemeManager.construct_gradient(val, 'background')
                    pseudo_states_qss += "}\n"
                elif 'pressed' in prop.lower():
                    pseudo_states_qss += f"{widget_class}:pressed {{\n"
                    pseudo_states_qss += ThemeManager.construct_gradient(val, 'background')
                    pseudo_states_qss += "}\n"
        return pseudo_states_qss

    @staticmethod
    def _build_subcontrols(widget_class, styles):
        """Build subcontrols for a widget."""
        subcontrols_qss = ""
        subcontrol_builders = {
            'up_down_buttons': ThemeManager._build_up_down_buttons,
            'indicator': ThemeManager._build_indicator,
            'chunk': ThemeManager._build_simple_subcontrol,
            'handle': ThemeManager._build_simple_subcontrol,
            'tab': ThemeManager._build_tab,
            'drop_down': ThemeManager._build_simple_subcontrol,
            'item': ThemeManager._build_simple_subcontrol
        }

        for prop, val in styles.items():
            if isinstance(val, dict):
                for key, builder in subcontrol_builders.items():
                    if key in prop.lower():
                        subcontrols_qss += builder(widget_class, key, val)
                        break
        return subcontrols_qss

    @staticmethod
    def _build_up_down_buttons(widget_class, _, val):
        """Build style for up-down buttons."""
        subcontrol = f"{widget_class}::up-button, {widget_class}::down-button"
        qss = f"{subcontrol} {{\n"
        for sub_prop, sub_val in val.items():
            if sub_prop not in ['hover', 'pressed']:
                if sub_prop in ['width', 'height']:
                    sub_val = ThemeManager.convert_to_percentage(sub_val)
                css_sub_prop = sub_prop.replace('_', '-')
                qss += f"    {css_sub_prop}: {sub_val};\n"
        qss += "}\n"

        for state in ['hover', 'pressed']:
            if state in val:
                qss += f"{subcontrol}:{state} {{\n"
                for state_prop, state_val in val[state].items():
                    css_state_prop = state_prop.replace('_', '-')
                    qss += f"    {css_state_prop}: {state_val};\n"
                qss += "}\n"
        return qss

    @staticmethod
    def _build_indicator(widget_class, _, val):
        """Build style for indicators."""
        subcontrol = f"{widget_class}::indicator"
        qss = f"{subcontrol} {{\n"
        for sub_prop, sub_val in val.items():
            if sub_prop not in ["checked", "unchecked", "hover"]:
                css_sub_prop = sub_prop.replace('_', '-')
                qss += f"    {css_sub_prop}: {sub_val};\n"
        qss += "}\n"

        for state in ["checked", "unchecked", "hover"]:
            if state in val:
                qss += f"{subcontrol}:{state} {{\n"
                for state_prop, state_val in val[state].items():
                    css_state_prop = state_prop.replace('_', '-')
                    qss += f"    {css_state_prop}: {state_val};\n"
                qss += "}\n"
        return qss

    @staticmethod
    def _build_simple_subcontrol(widget_class, key, val):
        """Build style for simple subcontrols."""
        subcontrol = f"{widget_class}::{key.replace('_', '-')}"
        qss = f"{subcontrol} {{\n"
        for sub_prop, sub_val in val.items():
            css_sub_prop = sub_prop.replace('_', '-')
            qss += f"    {css_sub_prop}: {sub_val};\n"
        qss += "}\n"
        return qss

    @staticmethod
    def _build_tab(widget_class, _, val):
        """Build style for tabs."""
        subcontrol = f"{widget_class}::tab"
        qss = f"{subcontrol} {{\n"
        for sub_prop, sub_val in val.items():
            if not isinstance(sub_val, dict):
                css_sub_prop = sub_prop.replace('_', '-')
                qss += f"    {css_sub_prop}: {sub_val};\n"
        qss += "}\n"

        for state in ['selected', 'hover']:
            if state in val:
                qss += f"{subcontrol}:{state} {{\n"
                for state_prop, state_val in val[state].items():
                    css_state_prop = state_prop.replace('_', '-')
                    qss += f"    {css_state_prop}: {state_val};\n"
                qss += "}\n"
        return qss

    @staticmethod
    def convert_to_percentage(value):
        """Convert pixel values to percentages if needed."""
        if isinstance(value, str) and value.endswith('px'):
            return value.replace('px', '%')
        return value

    @staticmethod
    def construct_gradient(gradient_dict, prop_name):
        """
        Construct a QSS gradient string from the gradient dictionary.
        """
        try:
            x1 = gradient_dict.get('x1', 0)
            y1 = gradient_dict.get('y1', 0)
            x2 = gradient_dict.get('x2', 0)
            y2 = gradient_dict.get('y2', 1)
            stops = gradient_dict.get('stops', {})
            stops_sorted = sorted(stops.items(), key=lambda item: float(item[0]))
            gradient = f"qlineargradient(x1:{x1}, y1:{y1}, x2:{x2}, y2:{y2}, "
            gradient += ", ".join([f"stop:{stop} {color}" for stop, color in stops_sorted])
            gradient += ")"
            return f"    {prop_name.replace('_', '-')} : {gradient};\n"
        except Exception as e:
            logger.error(f"Error constructing gradient for {prop_name}: {e}")
            message_collector.add_message("error_constructing_gradient", f"{prop_name}: {str(e)}")
            return ""
    
    @staticmethod
    def apply_palette(theme):
        """
        Apply the palette based on theme colors.
        """
        palette = QPalette()
        try:
            # Window
            window_color = QColor(theme.get('BASE', {}).get('primary_color', '#FFFFFF'))
            palette.setColor(QPalette.Window, window_color)

            # WindowText
            window_text_color = QColor(theme.get('BASE', {}).get('text_color', '#000000'))
            palette.setColor(QPalette.WindowText, window_text_color)

            # Base
            base_color = QColor(theme.get('QWidget_style', {}).get('background_color', '#FFFFFF'))
            palette.setColor(QPalette.Base, base_color)

            # AlternateBase
            alternate_base_color = QColor(theme.get('BASE', {}).get('secondary_color', '#F0F0F0'))
            palette.setColor(QPalette.AlternateBase, alternate_base_color)

            # ToolTipBase and ToolTipText
            tooltip_base = QColor(theme.get('TOOLTIP', {}).get('tooltip_background_gradient_start', '#FFFFFF'))
            tooltip_text = QColor(theme.get('TOOLTIP', {}).get('tooltip_text_color', '#000000'))
            palette.setColor(QPalette.ToolTipBase, tooltip_base)
            palette.setColor(QPalette.ToolTipText, tooltip_text)

            # Text
            text_color = QColor(theme.get('BASE', {}).get('text_color', '#000000'))
            palette.setColor(QPalette.Text, text_color)

            # Button
            button_color = QColor(theme.get('BUTTON', {}).get('button_background_gradient_start', '#FFFFFF'))
            palette.setColor(QPalette.Button, button_color)
            button_text_color = QColor(theme.get('BUTTON', {}).get('button_text_color', '#000000'))
            palette.setColor(QPalette.ButtonText, button_text_color)

            # Highlight
            highlight_color = QColor(theme.get('UI_ELEMENT', {}).get('selection_color', '#0000FF'))
            palette.setColor(QPalette.Highlight, highlight_color)
            highlighted_text_color = QColor(theme.get('BASE', {}).get('text_color', '#FFFFFF'))
            palette.setColor(QPalette.HighlightedText, highlighted_text_color)

            QApplication.instance().setPalette(palette)
            logger.debug("Palette applied successfully.")
            message_collector.add_message("palette_applied", f"CURRENT_THEME = {ThemeManager.current_theme_name}")
        except Exception as e:
            logger.error(f"Error applying palette: {e}")
            message_collector.add_message("error_applying_palette", f"Error applying palette: {str(e)}")

    @staticmethod
    def get_theme():
        if ThemeManager.current_theme is None:
            ThemeManager.apply_theme('dark')  # Default theme
        return ThemeManager.current_theme

    @staticmethod
    def get_int_value(value):
        try:
            return int(''.join(filter(str.isdigit, value)))
        except ValueError:
            logger.warning(f"Unable to convert '{value}' to integer.")
            message_collector.add_message("conversion_error", f"Unable to convert '{value}' to integer.")
            return 0

    @staticmethod
    def apply_widget_theme(widget: QWidget, theme_name: str):
        """
        Recursively apply theme to a widget and its children.
        """
        from Config.AppConfig.config import THEME_DEFAULTS
        
        theme = ThemeManager.get_theme()
        
        if isinstance(widget, QWidget):
            widget.setStyleSheet(f"""
                font-family: {theme.get('TYPOGRAPHY', {}).get('font_family', THEME_DEFAULTS['font_family'])};
                font-size: {theme.get('TYPOGRAPHY', {}).get('body_font_size', THEME_DEFAULTS['font_size'])};
            """)
        
        # Register text widgets for code block styling
        if isinstance(widget, (QTextEdit, QTextBrowser)):
            if not hasattr(QApplication.instance(), 'text_widgets'):
                QApplication.instance().text_widgets = []
            if widget not in QApplication.instance().text_widgets:
                QApplication.instance().text_widgets.append(widget)
                code_block_styles = theme.get('CODE_BLOCK_STYLE', {})
                apply_code_block_style(widget, code_block_styles)

        # Recursively apply to child widgets
        for child in widget.findChildren(QWidget):
            ThemeManager.apply_widget_theme(child, theme_name)

    @staticmethod
    def set_icon_theme(theme_name: str):
        """
        Implement icon theme switching logic here.
        This can involve setting icon paths based on the theme.
        """
        # Example placeholder implementation
        logger.info(f"Icon theme set to '{theme_name}'. (Implement as needed)")
        message_collector.add_message("icon_theme_set", f"ICON_THEME = {theme_name}")
        pass

    @staticmethod
    def get_color(color_name: str):
        theme = ThemeManager.get_theme()
        # Support nested keys using dot notation, e.g., "BASE.primary_color"
        keys = color_name.split('.')
        value = theme
        try:
            for key in keys:
                value = value[key]
            return value
        except KeyError:
            logger.warning(f"Color '{color_name}' not found in theme.")
            message_collector.add_message("color_not_found", f"Color '{color_name}' not found in theme.")
            return "#FFFFFF"  # Default color

    @staticmethod
    def get_font_size(size_name: str):
        theme = ThemeManager.get_theme()
        try:
            return theme['TYPOGRAPHY'][size_name]
        except KeyError:
            logger.warning(f"Font size '{size_name}' not found in theme.")
            message_collector.add_message("font_size_not_found", f"Font size '{size_name}' not found in theme.")
            return "14px"

    @staticmethod
    def get_spacing(spacing_name: str):
        theme = ThemeManager.get_theme()
        try:
            return theme['SPACING_AND_LAYOUT'][spacing_name]
        except KeyError:
            logger.warning(f"Spacing '{spacing_name}' not found in theme.")
            message_collector.add_message("spacing_not_found", f"Spacing '{spacing_name}' not found in theme.")
            return "8px"

    @staticmethod
    def update_main_window(main_window, theme_name):
        """
        Update the main window with the specified theme.
        """
        ThemeManager.apply_theme(theme_name)
        ThemeManager.apply_widget_theme(main_window, theme_name)
        ThemeManager.set_icon_theme(theme_name)
        logger.debug("Main window updated with the new theme.")
        message_collector.add_message("main_window_updated", f"MAIN_WINDOW_THEME = {theme_name}")

    @staticmethod
    def update_header_section(header_section, theme_name):
        """
        Update the header section with the specified theme.
        """
        ThemeManager.apply_theme(theme_name)
        theme = ThemeManager.get_theme()
        
        header_section.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme.get('OVERLAY_AND_SHADOW', {}).get('shadow_color')}, stop:1 {theme.get('BASE', {}).get('primary_color')});
            color: {theme.get('BASE', {}).get('text_color')};
            border-bottom: 1px solid {theme.get('UI_ELEMENT', {}).get('border_color')};
            font-family: {theme.get('TYPOGRAPHY', {}).get('font_family')};
        """)

        title = header_section.findChild(QLabel, "headerTitle")
        if title:
            title.setStyleSheet(f"""
                font-weight: bold;
                font-size: {theme.get('TYPOGRAPHY', {}).get('h3_font_size')};
                color: {theme.get('BASE', {}).get('text_color')};
                font-family: {theme.get('TYPOGRAPHY', {}).get('font_family')};
            """)

        button_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                padding: {theme.get('SPACING_AND_LAYOUT', {}).get('spacing_small')};
                border-radius: {theme.get('SPACING_AND_LAYOUT', {}).get('border_radius')};
            }}
            QPushButton:hover {{
                background-color: {theme.get('UI_ELEMENT', {}).get('hover_color')};
            }}
            QPushButton:pressed {{
                background-color: {theme.get('UI_ELEMENT', {}).get('active_color')};
            }}
        """

        for button_name in ['user', 'settings', 'moon']:
            button = header_section.findChild(QPushButton, f"headerButton_{button_name}")
            if button:
                button.setStyleSheet(button_style)
                logger.debug(f"Updated header button: {button_name}")
                message_collector.add_message("header_button_updated", f"BUTTON_NAME = {button_name}")

    @staticmethod
    def update_navigation_left_menu(navigation_left_menu, theme_name):
        """
        Update the navigation left menu with the specified theme.
        """
        ThemeManager.apply_theme(theme_name)
        theme = ThemeManager.get_theme()
        
        navigation_left_menu.setStyleSheet(f"""
            #navigationLeftMenu {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme.get('MENU', {}).get('menu_background_gradient_start')}, stop:1 {theme.get('MENU', {}).get('menu_background_gradient_end')});
                border-radius: {theme.get('SPACING_AND_LAYOUT', {}).get('border_radius')};
                margin-right: {theme.get('SPACING_AND_LAYOUT', {}).get('spacing_unit')};
            }}
            #navigationLeftMenuTitle {{
                font-weight: bold;
                font-size: {theme.get('TYPOGRAPHY', {}).get('h3_font_size')};
                color: {theme.get('BASE', {}).get('text_color')};
                padding: {theme.get('SPACING_AND_LAYOUT', {}).get('spacing_unit')};
                font-family: {theme.get('TYPOGRAPHY', {}).get('font_family')};
            }}
            QPushButton[objectName^="navigationLeftMenuButton_"] {{
                text-align: left;
                padding: {theme.get('MENU', {}).get('menu_item_padding')};
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme.get('MENU', {}).get('menu_background_gradient_start')}, stop:1 {theme.get('MENU', {}).get('menu_background_gradient_end')});
                color: {theme.get('MENU', {}).get('menu_text_color')};
                border: none;
                border-radius: {theme.get('SPACING_AND_LAYOUT', {}).get('border_radius')};
                font-size: {theme.get('TYPOGRAPHY', {}).get('body_font_size')};
                font-family: {theme.get('TYPOGRAPHY', {}).get('font_family')};
            }}
            QPushButton[objectName^="navigationLeftMenuButton_"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme.get('MENU', {}).get('menu_hover_background_gradient_start')}, stop:1 {theme.get('MENU', {}).get('menu_hover_background_gradient_end')});
            }}
            QPushButton[objectName^="navigationLeftMenuButton_"]:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme.get('MENU', {}).get('menu_active_background_gradient_start')}, stop:1 {theme.get('MENU', {}).get('menu_active_background_gradient_end')});
            }}
        """)

        logger.debug("Navigation left menu updated with the new theme.")
        message_collector.add_message("navigation_menu_updated", f"THEME_NAME = {theme_name}")

    @staticmethod
    def update_footer_frame(footer_frame, theme_name):
        """
        Update the footer frame with the specified theme.
        """
        try:
            if footer_frame is None:
                logger.error("Footer frame is None")
                return
                
            ThemeManager.apply_theme(theme_name)
            theme = ThemeManager.get_theme()
            
            # Main footer frame style
            try:
                footer_frame.setStyleSheet(f"""
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {theme.get('OVERLAY_AND_SHADOW', {}).get('shadow_color')}, stop:1 {theme.get('BASE', {}).get('secondary_color')});
                    color: {theme.get('BASE', {}).get('text_color')};
                    border-top: 1px solid {theme.get('UI_ELEMENT', {}).get('border_color')};
                """)
            except Exception as e:
                logger.error(f"Error setting footer frame stylesheet: {e}")
            
            # Label style
            label_style = f"""
                color: {theme.get('BASE', {}).get('subtext_color')};
                font-size: {theme.get('TYPOGRAPHY', {}).get('small_font_size')};
            """
            
            # Find and style the labels if they exist
            status_label = footer_frame.findChild(QLabel, "footerStatusLabel")
            version_label = footer_frame.findChild(QLabel, "footerVersionLabel")
            
            logger.debug(f"Found status label: {status_label is not None}")
            logger.debug(f"Found version label: {version_label is not None}")
            
            if status_label:
                try:
                    status_label.setStyleSheet(label_style)
                except Exception as e:
                    logger.error(f"Error setting status label stylesheet: {e}")
            
            if version_label:
                try:
                    version_label.setStyleSheet(label_style)
                except Exception as e:
                    logger.error(f"Error setting version label stylesheet: {e}")
            
            logger.debug("Footer frame updated with the new theme.")
            message_collector.add_message("footer_updated", f"THEME_NAME = {theme_name}")
            
        except Exception as e:
            logger.error(f"Error updating footer frame: {e}")
            message_collector.add_message("footer_update_error", f"ERROR = {str(e)}")

    @staticmethod
    def apply_code_block_style_to_all(code_block_styles):
        """
        Apply the code block style to all registered text widgets.

        Args:
            code_block_styles (dict): The code block style configurations from the theme.
        """
        if hasattr(QApplication.instance(), 'text_widgets'):
            for widget in QApplication.instance().text_widgets:
                apply_code_block_style(widget, code_block_styles)
            logger.debug("Applied code block styles to all registered text widgets.")
            message_collector.add_message("code_block_styles_applied", "CODE_BLOCK_STYLES = Applied to all text widgets")
        else:
            logger.warning("No text widgets registered to apply code block styles.")
            message_collector.add_message("no_text_widgets", "CODE_BLOCK_STYLES = No text widgets registered")

def apply_theme(widget: QWidget, theme_name: str):
    """
    Utility function to apply theme to the entire application and specific widgets.

    Args:
        widget (QWidget): The root widget to apply the theme to.
        theme_name (str): The name of the theme to apply.
    """
    try:
        ThemeManager.apply_theme(theme_name)
        ThemeManager.apply_widget_theme(widget, theme_name)
        ThemeManager.set_icon_theme(theme_name)
        logger.info(f"Theme '{theme_name}' applied successfully to widget and application.")
        message_collector.add_message("theme_applied", f"THEME_NAME = {theme_name}")
    except Exception as e:
        logger.error(f"Failed to apply theme '{theme_name}': {e}")
        message_collector.add_message("theme_application_failed", f"FAILED_THEME = {theme_name}, ERROR = {str(e)}")
