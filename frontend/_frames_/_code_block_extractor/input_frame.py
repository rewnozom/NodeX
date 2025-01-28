from PySide6.QtWidgets import QFrame, QVBoxLayout, QTextEdit, QPushButton, QLabel
from PySide6.QtCore import Signal

class InputFrame(QFrame):
    process_text_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Paste your text here and press Ctrl+Enter to process...")
        self.process_button = QPushButton("Process Text")
        self.process_button.clicked.connect(self.process_text)
        layout.addWidget(QLabel("Input Text:"))
        layout.addWidget(self.text_edit)
        layout.addWidget(self.process_button)

    def process_text(self):
        text = self.text_edit.toPlainText()
        self.process_text_signal.emit(text)

    def clear_text(self):
        self.text_edit.clear()