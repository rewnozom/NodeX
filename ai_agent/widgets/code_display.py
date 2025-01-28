# AI_Agent/widgets/code_display.py

import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                               QLineEdit, QTextEdit, QMessageBox, QFileDialog, QApplication)
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
import os
from log.logger import logger  # Custom logger import
from ..config.ai_config import SAVED_MODULES_DIR, DATAMEMORY_DIR, GROQ_OUTPUT_DIR_TEMPLATE

from Config.AppConfig.icon_config import (
    ICON_PATH,
    ICONS,
    ICON_NAMES,
)


logger = logging.getLogger(__name__)


def save_code_block(parent, code_block, filename=None, file_type=None, version=None):
    """
    Save the code block to a file, ensuring no overwrite.
    
    Args:
        parent (QWidget): Parent widget for dialog boxes.
        code_block (str): The code to be saved.
        filename (str): Optional filename. If not provided, file_type and version must be specified.
        file_type (str): Type of the file to be saved (if no filename is provided).
        version (str): Version of the saved code (if no filename is provided).
    """
    try:
        if filename:
            save_dir = SAVED_MODULES_DIR
            os.makedirs(save_dir, exist_ok=True)
            base_name, extension = os.path.splitext(filename)
            file_path = os.path.join(save_dir, filename)
            counter = 1
            while os.path.exists(file_path):
                file_path = os.path.join(save_dir, f"{base_name}({counter}){extension}")
                counter += 1
        else:
            if not file_type or not version:
                raise ValueError("file_type and version must be specified if filename is not provided.")
            directory = GROQ_OUTPUT_DIR_TEMPLATE.format(version=version)
            os.makedirs(directory, exist_ok=True)
            file_path = os.path.join(directory, f"code_block{file_type}")

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(code_block)
        
        logger.info(f"Code block successfully saved as {file_path}.")
        QMessageBox.information(parent, "Saved", f"Code saved to {file_path}")
    except Exception as e:
        logger.error(f"Unexpected error saving code block: {e}")
        QMessageBox.warning(parent, "Error", f"Failed to save code: {e}")

def update_code_block_in_datamemory(parent, filename, code_block):
    """
    Update a code block in the datamemory folder.

    Args:
        parent (QWidget): Parent widget for dialog boxes.
        filename (str): The name of the file to update.
        code_block (str): The updated code to be written.
    """
    file_path = os.path.join(DATAMEMORY_DIR, filename)
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(code_block)
        logger.info(f"Code block successfully updated in {file_path}.")
        QMessageBox.information(parent, "Updated", f"Code block updated in {file_path}")
    except Exception as e:
        logger.error(f"Unexpected error updating code block in datamemory: {e}")
        QMessageBox.warning(parent, "Error", f"Failed to update code block: {e}")

def read_file_from_datamemory(filename):
    """
    Read content from a file in the datamemory folder.

    Args:
        filename (str): The name of the file to be read.

    Returns:
        str: The content of the file, or None if there was an error.
    """
    filepath = os.path.join(DATAMEMORY_DIR, filename)
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                logger.info(f"File {filename} successfully read from datamemory.")
                return content
    except Exception as e:
        logger.error(f"Unexpected error reading file from datamemory: {e}")
    return None


class CodeDisplayWindow(QWidget):
    def __init__(self, code_block, language='python'):
        super().__init__()
        self.code_block = code_block
        self.language = language
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Code Block Viewer")
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        width = screen_geometry.width() * 0.6  # 60% of screen width
        height = screen_geometry.height() * 0.6  # 60% of screen height
        self.setGeometry((screen_geometry.width() - width) / 2,
                         (screen_geometry.height() - height) / 2,
                         width, height)
        self.setStyleSheet("background-color: #2e2e2e; color: #ffffff;")

        layout = QVBoxLayout()

        # Buttons Layout
        buttons_layout = QHBoxLayout()

        # Copy Button
        copy_button = QPushButton("Copy Code")
        copy_button.setIcon(QIcon(ICONS.get('copy', '')))  # Ensure 'copy' icon exists in ICONS
        copy_button.clicked.connect(self.copy_code_to_clipboard)
        buttons_layout.addWidget(copy_button)

        # Save Button
        save_button = QPushButton("Save Code")
        save_button.setIcon(QIcon(ICONS.get('save', '')))  # Ensure 'save' icon exists in ICONS
        save_button.clicked.connect(self.save_code)
        buttons_layout.addWidget(save_button)

        layout.addLayout(buttons_layout)

        # Language Label
        language_label = QLabel(f"Language: {self.language}")
        layout.addWidget(language_label)

        # Code Display
        self.code_text = QTextEdit()
        self.code_text.setPlainText(self.code_block)
        self.code_text.setReadOnly(True)
        self.code_text.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        font = QFont("Consolas", 10)  # Reduced font size
        self.code_text.setFont(font)
        layout.addWidget(self.code_text)

        self.setLayout(layout)

    def copy_code_to_clipboard(self):
        """
        Copy the entire code block to the clipboard.
        """
        try:
            QApplication.clipboard().setText(self.code_block)
            QMessageBox.information(self, "Copied", "Code copied to clipboard!")
            logger.info("Code block copied to clipboard.")
        except Exception as e:
            logger.error(f"Error copying code to clipboard: {e}")
            QMessageBox.warning(self, "Error", f"Failed to copy code: {e}")

    def save_code(self):
        """
        Save the code block to a file.
        """
        try:
            # Add your save logic here
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Code", "", "All Files (*)", options=options)
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.code_block)
                QMessageBox.information(self, "Saved", f"Code saved to {file_path}")
                logger.info(f"Code block saved to {file_path}.")
        except Exception as e:
            logger.error(f"Unexpected error saving code block: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save code block: {e}")


# Utility function to copy text to the clipboard
def copy_to_clipboard(text):
    """Copy text to clipboard."""
    try:
        QApplication.clipboard().setText(text)
        QMessageBox.information(None, "Copied", "Text copied to clipboard!")
        logger.info("Copied text to clipboard.")
    except Exception as e:
        logger.error(f"Unexpected error copying to clipboard: {e}")


# Utility function to show a code display window
def show_code_window(code_block, language='python'):
    """
    Display a new window showing the code block.
    Args:
        code_block (str): The code block to be displayed in the window.
        language (str): The programming language of the code block.
    """
    try:
        logger.debug(f"Showing code window with code block:\n{code_block}")
        code_window = CodeDisplayWindow(code_block, language=language)
        code_window.show()
        logger.info("Code window displayed successfully.")
    except Exception as e:
        logger.error(f"Unexpected error showing code window: {e}")
