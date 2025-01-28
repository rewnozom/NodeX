# ..\ai_agent\config\ai_config.py

import os
import json
import logging
from PySide6.QtWidgets import QListWidget, QLineEdit
from PySide6.QtCore import Qt

# Constants
MEMORY_FILE_PATH = "./Workspace/memory.json"

logger = logging.getLogger(__name__)

def save_memory(memory):
    """Save memory to memory.json file."""
    try:
        with open(MEMORY_FILE_PATH, 'w') as file:
            json.dump(memory, file)
        logger.info("Memory successfully saved.")
    except Exception as e:
        logger.error(f"Unexpected error saving memory: {e}")

def load_memory():
    """Load memory from memory.json file."""
    try:
        if os.path.exists(MEMORY_FILE_PATH):
            with open(MEMORY_FILE_PATH, 'r') as file:
                return json.load(file)
        else:
            logger.info("No memory file found.")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error while loading memory: {e}")
    except Exception as e:
        logger.error(f"Unexpected error loading memory: {e}")
    return []

def add_memory(memory_listwidget, memory_entry_widget, additional_memory):
    """Add an entry to the memory list widget and update the memory file."""
    try:
        memory_entry = memory_entry_widget.text()
        if memory_entry.strip():
            additional_memory.append({"role": "system", "content": memory_entry})
            memory_listwidget.addItem(memory_entry)
            memory_entry_widget.setText("")
            save_memory(additional_memory)
            logger.info(f"Memory entry added: {memory_entry}")
        else:
            logger.warning("Attempted to add an empty memory entry.")
    except Exception as e:
        logger.error(f"Unexpected error adding memory: {e}")

def remove_memory(memory_listwidget, additional_memory):
    """Remove selected entries from the memory list widget and update the memory file."""
    try:
        selected_items = memory_listwidget.selectedItems()
        for item in selected_items:
            index = memory_listwidget.row(item)
            removed_entry = additional_memory.pop(index)
            memory_listwidget.takeItem(index)
            logger.info(f"Memory entry removed: {removed_entry}")
        save_memory(additional_memory)
    except Exception as e:
        logger.error(f"Unexpected error removing memory: {e}")
