import os
import pytest
from unittest.mock import MagicMock
from ai_agent.memory.memory_manager import (
    save_memory, load_memory, add_memory, remove_memory
)

def test_save_load_memory(temp_dir):
    test_memory_file = os.path.join(temp_dir, "memory.json")
    test_memory = [
        {"role": "system", "content": "Test memory 1"},
        {"role": "user", "content": "Test memory 2"}
    ]
    save_memory(test_memory, test_memory_file)
    loaded = load_memory(test_memory_file)
    assert loaded == test_memory

def test_add_memory():
    memory_listwidget = MagicMock()
    memory_entry_widget = MagicMock()
    memory_entry_widget.text.return_value = "New memory"
    additional_memory = []

    add_memory(memory_listwidget, memory_entry_widget, additional_memory)
    assert len(additional_memory) == 1
    assert additional_memory[0]["content"] == "New memory"
    memory_listwidget.addItem.assert_called_once()

def test_remove_memory():
    memory_listwidget = MagicMock()
    # Suppose we have 2 selected items
    memory_listwidget.selectedItems.return_value = [MagicMock(), MagicMock()]
    # Rows 0, 1 for these items
    memory_listwidget.row.side_effect = [0, 1]
    additional_memory = [
        {"role": "system", "content": "Memory 1"},
        {"role": "system", "content": "Memory 2"},
        {"role": "system", "content": "Memory 3"}
    ]

    remove_memory(memory_listwidget, additional_memory)
    assert len(additional_memory) == 1
    memory_listwidget.takeItem.assert_called()
