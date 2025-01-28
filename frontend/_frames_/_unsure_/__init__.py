from ..page.desktop.main_window import App
from .sidebar import SidebarFrame
from .settings_tab import TabViewFrame
from .sliders_progress_frame import SliderProgressbarFrame
from .radio_buttons_frame import RadiobuttonFrame
from .entry_run_frame import EntryRunFrame
from .checkbox_frame import CheckboxFrame
from .scrollable_textbox_frame import ScrollableTextboxFrame  # Added this

__all__ = [
    'App',
    'SidebarFrame',
    'TabViewFrame',
    'SliderProgressbarFrame',
    'RadiobuttonFrame',
    'EntryRunFrame',
    'CheckboxFrame',
    'ScrollableTextboxFrame'  # Added this
]