# ./settings/SettingWidgetGroup.py

from dataclasses import dataclass
from typing import Optional

from PySide6.QtWidgets import QLabel, QLineEdit


@dataclass
class SettingWidgetGroup:
    """Data class to keep track of related widgets for each setting"""
    label: QLabel
    editor: QLineEdit
    buttons: Optional[list] = None