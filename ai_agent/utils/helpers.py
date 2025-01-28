# AI_Agent/utils/helpers.py

import os
import logging
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QMenu, QFileDialog, QMessageBox
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)

DATAMEMORY_DIR = "./Workspace/datamemory"

def handle_file_patterns(user_message):
    """Handle @filename and @@filename patterns in the user message."""
    # Implement the logic to handle file patterns
    # For now, let's assume it returns the message unchanged
    return user_message, {}

def insert_file_name(user_message_textedit, file_name):
    """Insert the file name into the user message text edit."""
    try:
        cursor = user_message_textedit.textCursor()
        cursor.insertText(file_name)
        user_message_textedit.setTextCursor(cursor)
        logger.info(f"File name {file_name} inserted into the user message.")
    except Exception as e:
        logger.error(f"Unexpected error inserting file name: {e}")

def show_file_suggestions(user_message_textedit):
    """Show a context menu with file suggestions from the datamemory folder."""
    cursor = user_message_textedit.textCursor()
    pos = user_message_textedit.cursorRect(cursor).bottomRight()
    global_pos = user_message_textedit.mapToGlobal(pos)

    menu = QMenu(user_message_textedit)
    try:
        files = os.listdir(DATAMEMORY_DIR)
    except FileNotFoundError:
        files = []
    for file in files:
        action = QAction(file, user_message_textedit)
        action.triggered.connect(lambda checked, f=file: insert_file_name(user_message_textedit, f))
        menu.addAction(action)
    menu.exec(global_pos)

def auto_suggest_files(event, user_message_textedit):
    """Auto-suggest files in the datamemory folder based on user input."""
    try:
        cursor = user_message_textedit.textCursor()
        pos = user_message_textedit.cursorRect(cursor).bottomRight()
        global_pos = user_message_textedit.mapToGlobal(pos)

        menu = QMenu(user_message_textedit)
        files = os.listdir(DATAMEMORY_DIR)
        for file in files:
            action = QAction(file, user_message_textedit)
            action.triggered.connect(lambda checked, f=file: insert_file_name(user_message_textedit, f))
            menu.addAction(action)
        menu.exec(global_pos)
    except Exception as e:
        logger.error(f"Unexpected error in auto_suggest_files: {e}")

def handle_file_drop(event, user_message_widget):
    """Handle file drop event."""
    try:
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            with open(file_path, 'r') as file:
                file_content = file.read()
            user_message_widget.insertPlainText(f"\n\nDropped file content:\n{file_content}")
            logger.info(f"Handled file drop from {file_path}.")
        else:
            logger.warning("No file was dropped.")
    except Exception as e:
        logger.error(f"Unexpected error handling file drop: {e}")

def handle_file_upload(parent_widget):
    """Upload a file to the datamemory folder."""
    file_dialog = QFileDialog(parent_widget)
    file_path, _ = file_dialog.getOpenFileName()
    if file_path:
        try:
            os.makedirs(DATAMEMORY_DIR, exist_ok=True)
            file_name = os.path.basename(file_path)
            destination = os.path.join(DATAMEMORY_DIR, file_name)
            with open(file_path, 'rb') as src, open(destination, 'wb') as dst:
                dst.write(src.read())
            QMessageBox.information(parent_widget, "Success", f"File '{file_name}' uploaded successfully.")
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            QMessageBox.critical(parent_widget, "Error", f"Failed to upload file: {e}")

def view_uploaded_files(parent_widget):
    """View files in the datamemory folder."""
    try:
        files = os.listdir(DATAMEMORY_DIR)
        if not files:
            QMessageBox.information(parent_widget, "No Files", "No files uploaded yet.")
            return
        file_list = "\n".join(files)
        QMessageBox.information(parent_widget, "Uploaded Files", file_list)
    except FileNotFoundError:
        QMessageBox.warning(parent_widget, "Directory Not Found", "The datamemory directory does not exist.")
