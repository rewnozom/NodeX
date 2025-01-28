# ./utils/card_utils.py
from PySide6.QtWidgets import QFrame, QVBoxLayout

def create_card(title: str = "", padding: int = 10) -> QFrame:
    """
    Create a card-like frame with a dark background, rounded corners,
    and an optional title area.
    """
    card = QFrame()
    card.setStyleSheet("""
        QFrame {
            background-color: #2E2E2E;
            border: 1px solid #555;
            border-radius: 8px;
        }
    """)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(padding, padding, padding, padding)
    layout.setSpacing(10)
    if title:
        from PySide6.QtWidgets import QLabel
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold; background: transparent;")
        layout.addWidget(title_label)
    return card
