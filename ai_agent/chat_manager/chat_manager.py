# AI_Agent/chat_manager/chat_manager.py

import json
import os
import shutil
import re
from datetime import datetime

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import QListWidgetItem, QInputDialog, QMessageBox, QFileDialog

from log.logger import logger  # Custom logger import
from ai_agent.config.ai_config import CHAT_HISTORY_FOLDER  # Import constants from ai_config
from ai_agent.memory.memory_manager import load_memory
from ai_agent.code_block_manager.code_block_manager import (
    read_file_from_datamemory, update_code_block_in_datamemory
)


# Constants
CHAT_HISTORY_DIR = CHAT_HISTORY_FOLDER

class ShortTermHistory(QObject):
    """
    Class to manage short-term chat history.
    """
    history_updated = Signal()

    def __init__(self, history_file=None):
        super().__init__()
        if history_file is None:
            history_file = os.path.join(CHAT_HISTORY_DIR, "chat_history.json")
        self.history_file = history_file
        self.history = self.load_history()

    def load_history(self):
        """Load history from JSON file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return []
            except Exception as e:
                logger.error(f"Error loading history: {e}")
                return []
        else:
            return []

    def add_event(self, event):
        """Add an event to the history."""
        self.history.append(event)
        self.save_history()
        self.history_updated.emit()

    def save_history(self):
        """Save history to JSON file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
            logger.info("History successfully saved.")
        except Exception as e:
            logger.error(f"Error saving history: {e}")


def save_chat_log(chat_id, chat_data):
    """
    Save chat history to a JSON file.
    """
    if not os.path.exists(CHAT_HISTORY_DIR):
        os.makedirs(CHAT_HISTORY_DIR)
    file_path = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, ensure_ascii=False, indent=4)
        logger.info(f"Chat log saved for chat_id {chat_id}")
    except Exception as e:
        logger.error(f"Error saving chat log for chat_id {chat_id}: {e}")


def load_history():
    """
    Load all chat IDs from the chat history directory.
    """
    if not os.path.exists(CHAT_HISTORY_DIR):
        os.makedirs(CHAT_HISTORY_DIR)
    return [fname[:-5] for fname in os.listdir(CHAT_HISTORY_DIR) if fname.endswith('.json')]


def load_chat_log(chat_id):
    """
    Load a selected chat by chat ID.
    """
    file_path = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON for chat_id {chat_id}: {e}")
            return {'title': 'New Chat', 'messages': []}
        except Exception as e:
            logger.error(f"Error loading chat log for chat_id {chat_id}: {e}")
            return {'title': 'New Chat', 'messages': []}
    else:
        return {'title': 'New Chat', 'messages': []}


def clear_chat(chat_id, chats, chat_display):
    """
    Clears the chat with the given ID.
    Args:
        chat_id (str): The ID of the chat to clear.
        chats (dict): The dictionary of all chats.
        chat_display (QWidget): The widget displaying the chat.
    """
    if chat_id in chats:
        chats[chat_id]['messages'] = []
        chat_display.setMarkdown("")
    else:
        raise ValueError(f"Chat ID {chat_id} not found.")


def process_files(input_dir, output_dir, system_prompt, llm, progress_callback=None, is_running=lambda: True):
    """
    Process files in the input directory and save results to the output directory.
    
    Args:
        input_dir (str): Path to the input directory.
        output_dir (str): Path to the output directory.
        system_prompt (str): System prompt to guide processing.
        llm (object): The language model instance.
        progress_callback (callable): Optional callback for progress updates.
        is_running (callable): Function to check if the process should continue.
    """
    import os
    import shutil

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    for file_name in os.listdir(input_dir):
        if not is_running():
            break

        input_path = os.path.join(input_dir, file_name)
        output_path = os.path.join(output_dir, f"processed_{file_name}")

        # Simulate file processing
        if progress_callback:
            progress_callback(file_name, "Processing")

        try:
            with open(input_path, "r") as f:
                content = f.read()
            processed_content = llm.process(content, system_prompt)
            with open(output_path, "w") as f:
                f.write(processed_content)

            if progress_callback:
                progress_callback(file_name, "Completed")

        except Exception as e:
            if progress_callback:
                progress_callback(file_name, f"Error: {e}")
            continue


def delete_chat_log(chat_id):
    """
    Delete a chat log by chat ID.
    """
    file_path = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Chat log deleted for chat_id {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting chat log for chat_id {chat_id}: {e}")
            return False
    else:
        logger.warning(f"Chat log file does not exist for chat_id {chat_id}")
        return False


def load_chat_history(chat_history_list):
    """
    Load chat history files into the chat history list.
    """
    try:
        chat_history_list.clear()
        chat_ids = load_history()
        for chat_id in chat_ids:
            chat_data = load_chat_log(chat_id)
            chat_title = chat_data.get('title', 'Untitled Chat')
            item = QListWidgetItem(chat_title)
            item.setData(Qt.UserRole, chat_id)
            chat_history_list.addItem(item)
        logger.info("Chat history loaded.")
    except Exception as e:
        logger.error(f"Error loading chat history: {e}")


def start_new_chat(chats, chat_history_list, chat_display):
    """
    Start a new chat session.
    """
    chat_id = datetime.now().strftime("%Y%m%d%H%M%S")
    chat_data = {'title': 'New Chat', 'messages': []}
    chats[chat_id] = chat_data

    # Add to chat history list
    item = QListWidgetItem(chat_data['title'])
    item.setData(Qt.UserRole, chat_id)
    chat_history_list.addItem(item)
    chat_history_list.setCurrentItem(item)

    # Clear chat display
    chat_display.clear()

    # Save the new chat
    save_chat_log(chat_id, chat_data)

    return chat_id


def switch_chat(chat_id, chats, chat_display):
    """
    Switch to a selected chat session.
    """
    # Load messages from the chat log
    chat_data = load_chat_log(chat_id)
    chats[chat_id] = chat_data

    chat_display.clear()
    return chat_data['messages']


def add_to_chat_history(chat_id, chats, message):
    """
    Add a message to the current chat's history.
    """
    chats[chat_id]['messages'].append(message)
    # Save the chat log
    save_chat_log(chat_id, chats[chat_id])


def new_chat(chat_display, user_message_var):
    """
    Start a new chat session by clearing the chat display and input field.
    """
    try:
        # Clear chat display (QTextEdit in PySide)
        chat_display.clear()

        # Clear input field (QLineEdit in PySide)
        user_message_var.clear()
        
        logger.info("New chat session started.")
    except Exception as e:
        logger.error(f"Unexpected error starting new chat: {e}")


def load_selected_chat(chat_id):
    """
    Load a specific chat based on chat ID.
    """
    file_path = os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON for chat_id {chat_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading chat for chat_id {chat_id}: {e}")
            return None
    else:
        logger.warning(f"No chat log found for chat_id {chat_id}")
        return None


def rename_selected_chat(chat_history_list, chats):
    """
    Rename the selected chat in the chat history.
    """
    item = chat_history_list.currentItem()
    if item:
        new_title, ok = QInputDialog.getText(None, "Rename Chat", "Enter new chat name:")
        if ok and new_title.strip():
            chat_id = item.data(Qt.UserRole)
            chats[chat_id]['title'] = new_title.strip()
            item.setText(new_title.strip())
            # Save the chat data with the new title
            save_chat_log(chat_id, chats[chat_id])
        else:
            QMessageBox.warning(None, "Invalid Input", "Chat name cannot be empty.")
    else:
        QMessageBox.warning(None, "No Chat Selected", "Please select a chat to rename.")


def delete_selected_chat(chat_history_list, chats):
    """
    Delete the selected chat from the chat history.
    """
    item = chat_history_list.currentItem()
    if item:
        reply = QMessageBox.question(
            None, "Delete Chat",
            "Are you sure you want to delete this chat?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            chat_id = item.data(Qt.UserRole)
            # Delete chat log file
            success = delete_chat_log(chat_id)
            if success:
                del chats[chat_id]
                chat_history_list.takeItem(chat_history_list.row(item))
                return True
            else:
                QMessageBox.warning(None, "Delete Failed", "Failed to delete the chat log file.")
    else:
        QMessageBox.warning(None, "No Chat Selected", "Please select a chat to delete.")
    return False


def upload_file(parent):
    """
    Upload a file to the datamemory folder.
    """
    file_path, _ = QFileDialog.getOpenFileName(parent, "Upload File")
    if file_path:
        try:
            os.makedirs("./Workspace/datamemory", exist_ok=True)
            shutil.copy(file_path, "./Workspace/datamemory")
            QMessageBox.information(parent, "Upload Successful", f"File {os.path.basename(file_path)} uploaded successfully.")
        except Exception as e:
            QMessageBox.warning(parent, "Upload Error", f"An error occurred while uploading the file: {e}")


def view_files(parent):
    """
    View files in the datamemory folder.
    """
    files = os.listdir("./Workspace/datamemory")
    file_dialog = QFileDialog(parent)
    file_dialog.setWindowTitle("Files in Datamemory")
    file_dialog.setFileMode(QFileDialog.ExistingFile)
    file_dialog.setNameFilter("All Files (*)")
    file_dialog.setDirectory("./Workspace/datamemory")
    
    if file_dialog.exec_():
        selected_files = file_dialog.selectedFiles()
        if selected_files:
            selected_file = selected_files[0]
            QMessageBox.information(parent, "File Selected", f"Selected file: {os.path.basename(selected_file)}")


def rename_file(parent, file_path):
    """
    Rename a file in the datamemory folder.
    """
    old_name = os.path.basename(file_path)
    new_name, ok = QInputDialog.getText(parent, "Rename File", "Enter new name:", text=old_name)
    if ok and new_name and new_name != old_name:
        try:
            new_path = os.path.join(os.path.dirname(file_path), new_name)
            os.rename(file_path, new_path)
            QMessageBox.information(parent, "Rename Successful", f"File renamed to {new_name}.")
        except Exception as e:
            QMessageBox.warning(parent, "Rename Error", f"An error occurred while renaming the file: {e}")


def delete_file(parent, file_path):
    """
    Delete a file from the datamemory folder.
    """
    reply = QMessageBox.question(
        parent, "Delete File",
        f"Are you sure you want to delete {os.path.basename(file_path)}?",
        QMessageBox.Yes | QMessageBox.No
    )
    if reply == QMessageBox.Yes:
        try:
            os.remove(file_path)
            QMessageBox.information(parent, "Delete Successful", f"File {os.path.basename(file_path)} deleted successfully.")
        except Exception as e:
            QMessageBox.warning(parent, "Delete Error", f"An error occurred while deleting the file: {e}")


def get_file_language(filename):
    """
    Determine the language of the file for code block formatting.

    Args:
        filename (str): The filename.

    Returns:
        str: The language string.
    """
    if filename.endswith('.py'):
        return 'python'
    elif filename.endswith('.md'):
        return 'markdown'
    elif filename.endswith('.json'):
        return 'json'
    elif filename.endswith('.js'):
        return 'javascript'
    elif filename.endswith('.ts'):
        return 'typescript'
    else:
        return ''


def handle_file_patterns(user_message):
    """
    Handle @filename and @@filename patterns in the user message.

    Args:
        user_message (str): The user's message.

    Returns:
        tuple: Updated user message and file contents dictionary.
    """
    file_pattern = r'@(\w+\.\w+)'
    update_file_pattern = r'@@(\w+\.\w+)'
    matches = re.findall(file_pattern, user_message)
    update_matches = re.findall(update_file_pattern, user_message)
    file_contents = {}

    for match in matches:
        if match not in file_contents:
            file_content = read_file_from_datamemory(match)
            if file_content:
                file_contents[match] = file_content
                user_message = user_message.replace(f"@{match}", f"```{get_file_language(match)}\n{file_content}\n```")
                logger.info(f"File content added for {match}")

    for match in update_matches:
        file_content = read_file_from_datamemory(match)
        if file_content:
            file_contents[match] = file_content
            user_message = user_message.replace(f"@@{match}", f"```{get_file_language(match)}\n{file_content}\n```")
            update_code_block_in_datamemory(match, file_content)
            logger.info(f"File content updated for {match}")

    return user_message, file_contents


def prepare_messages(system_message, user_message, current_model_name, config):
    """
    Prepare the messages for the AI model.

    Args:
        system_message (str): The system prompt.
        user_message (str): The user's message.
        current_model_name (str): The name of the current model.
        config: Configuration object.

    Returns:
        list or str: A list of messages or a concatenated string, depending on the model.
    """
    # For models that accept message lists
    messages = []
    if current_model_name in ['OpenAI Chat Model', 'GPT-4', 'GPT-3.5-Turbo']:
        messages.append({"role": "system", "content": system_message})
        if config.ENABLE_MEMORY:
            additional_memory = load_memory()
            messages += [{"role": m["role"], "content": m["content"]} for m in additional_memory if m["content"]]
        messages.append({"role": "user", "content": user_message})
        messages = [m for m in messages if m["content"]]  # Filter out any empty messages
    else:
        # For models that accept plain text
        messages = system_message + "\n" + user_message
    return messages
