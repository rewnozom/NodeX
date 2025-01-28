# AI_Agent/code_block_manager/code_block_manager.py

import os
from PySide6.QtWidgets import QMessageBox
from log.logger import logger  # Custom logger import
from ..config.ai_config import SAVED_MODULES_DIR, DATAMEMORY_DIR, GROQ_OUTPUT_DIR_TEMPLATE

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
