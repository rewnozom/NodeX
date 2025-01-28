# AI_Agent/utils/key_bindings.py

import logging
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtCore import Qt
logger = logging.getLogger(__name__)

class KeyBindings:
    def __init__(self, app):
        """
        Initialize key bindings for the given application.
        The app should have a QTextEdit (or compatible) widget to bind keys to.
        """
        self.app = app
        self._setup_key_bindings()

    def _setup_key_bindings(self):
        """Setup key bindings for copy, paste, and undo using PySide6."""
        self.app.code_text.keyPressEvent = self.key_press_event_override  # Override key press events

    def key_press_event_override(self, event):
        """Handle key press events and map them to the appropriate functions."""
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_C:
                self.copy()
            elif event.key() == Qt.Key_V:
                self.paste()
            elif event.key() == Qt.Key_Z:
                self.undo()
        else:
            # Call the default event handler for other keys
            super(self.app.code_text.__class__, self.app.code_text).keyPressEvent(event)

    def copy(self):
        """Copy selected text to clipboard."""
        try:
            selected_text = self.app.code_text.textCursor().selectedText()
            if selected_text:
                QApplication.clipboard().setText(selected_text)
                QMessageBox.information(self.app, "Copied", "Selected text copied to clipboard.")
                logger.info(f"Copied to clipboard: {selected_text}")
            else:
                logger.warning("No text selected to copy.")
        except Exception as e:
            logger.error(f"Copy operation failed: {e}")

    def paste(self):
        """Paste text from clipboard."""
        try:
            clipboard_text = QApplication.clipboard().text()
            if clipboard_text:
                cursor = self.app.code_text.textCursor()
                cursor.insertText(clipboard_text)
                logger.info(f"Pasted text from clipboard: {clipboard_text}")
            else:
                logger.warning("Clipboard is empty.")
        except Exception as e:
            logger.error(f"Paste operation failed: {e}")

    def undo(self):
        """Undo the last action in the QTextEdit."""
        try:
            self.app.code_text.undo()
            logger.info("Undo operation successful.")
        except Exception as e:
            logger.error(f"Undo operation failed: {e}")
