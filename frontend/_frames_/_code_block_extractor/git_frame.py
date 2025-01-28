from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QTextEdit
from PySide6.QtCore import Signal

class GitFrame(QFrame):
    commit_changes_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.commit_button = QPushButton("Commit Changes")
        self.commit_button.clicked.connect(self.commit_changes)
        self.diff_display = QTextEdit()
        self.diff_display.setReadOnly(True)
        layout.addWidget(self.commit_button)
        layout.addWidget(self.diff_display)

    def commit_changes(self):
        # Emit a signal to request commit message from the user
        self.commit_changes_signal.emit("Commit Changes")

    def update_diff(self, diff):
        self.diff_display.setPlainText(diff)