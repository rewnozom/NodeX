# pages/qframes/GitFrame/GitFrame.py

from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QTextEdit, QLabel, QHBoxLayout, QMessageBox
from PySide6.QtCore import Signal
from .._helper.GitManager import GitManager

class GitFrame(QFrame):
    """
    Manages Git operations like committing changes and showing diffs.
    """
    def __init__(self, repo_path: str, parent=None):
        super().__init__(parent)
        self.git_manager = GitManager(repo_path)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Git Buttons
        git_buttons_layout = QHBoxLayout()
        self.commitButton = QPushButton("Commit Changes")
        self.commitButton.clicked.connect(self.commitChanges)
        self.diffButton = QPushButton("Show Diff")
        self.diffButton.clicked.connect(self.showDiff)
        git_buttons_layout.addWidget(self.commitButton)
        git_buttons_layout.addWidget(self.diffButton)
        layout.addLayout(git_buttons_layout)

        # Diff Display
        self.diffDisplay = QTextEdit()
        self.diffDisplay.setReadOnly(True)
        layout.addWidget(QLabel("Git Diff:"))
        layout.addWidget(self.diffDisplay)

        self.setLayout(layout)

    def commitChanges(self):
        """
        Commits changes to the Git repository with a user-provided message.
        """
        message, ok = self.getTextInput("Commit Changes", "Enter commit message:")
        if ok and message:
            try:
                self.git_manager.commit_changes(message)
                QMessageBox.information(self, "Git", "Changes committed successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Git Error", str(e))

    def showDiff(self):
        """
        Shows the current Git diff in the diff display area.
        """
        diff = self.git_manager.get_diff()
        self.diffDisplay.setPlainText(diff if diff else "No changes detected.")

    def getTextInput(self, title: str, label: str):
        """
        Prompts the user to enter text input via a dialog.
        """
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, title, label)
        return text, ok
