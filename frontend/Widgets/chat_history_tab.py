from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton, QMessageBox


from PySide6.QtCore import Qt
from ai_agent.chat_manager.chat_manager import (
    load_chat_history, start_new_chat, switch_chat,
    rename_selected_chat, delete_selected_chat, clear_chat
)
from log.logger import logger

class ChatHistoryTab(QWidget):
    def __init__(self, parent=None, chat_display=None, chats=None):
        super().__init__(parent)
        self.chat_display = chat_display
        self.chats = chats

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Chat History Title
        chat_history_title = QLabel("Chat History")
        chat_history_title.setAlignment(Qt.AlignCenter)
        chat_history_title.setObjectName("chatHistoryTitle")  # For theming
        layout.addWidget(chat_history_title)

        # Chat History List
        self.chat_history_list = QListWidget()
        self.chat_history_list.setObjectName("chatHistoryList")  # For theming
        layout.addWidget(self.chat_history_list)

        # Chat History Buttons
        self.load_chat_button = QPushButton("Load Selected Chat")
        self.new_chat_button = QPushButton("New Chat")
        self.rename_chat_button = QPushButton("Rename Selected Chat")
        self.delete_chat_button = QPushButton("Delete Selected Chat")
        self.clear_chat_button = QPushButton("Clear Chat")
        layout.addWidget(self.load_chat_button)
        layout.addWidget(self.new_chat_button)
        layout.addWidget(self.rename_chat_button)
        layout.addWidget(self.delete_chat_button)
        layout.addWidget(self.clear_chat_button)

        # Connect signals
        self.new_chat_button.clicked.connect(self.start_new_chat)
        self.load_chat_button.clicked.connect(self.load_selected_chat)
        self.rename_chat_button.clicked.connect(self.rename_selected_chat)
        self.delete_chat_button.clicked.connect(self.delete_selected_chat)
        self.clear_chat_button.clicked.connect(self.clear_current_chat)
        self.chat_history_list.itemClicked.connect(self.switch_chat)

        # Load chat history
        self.load_chat_history()

    def load_chat_history(self):
        load_chat_history(self.chat_history_list)

    def start_new_chat(self):
        chat_id = start_new_chat(self.chats, self.chat_history_list, self.chat_display)
        logger.info(f"Started new chat with ID: {chat_id}")

    def load_selected_chat(self):
        item = self.chat_history_list.currentItem()
        if item:
            switch_chat(item.data(Qt.UserRole), self.chats, self.chat_display)
            logger.info(f"Loaded chat: {item.text()}")
        else:
            QMessageBox.warning(self, "No Chat Selected", "Please select a chat to load.")

    def rename_selected_chat(self):
        item = self.chat_history_list.currentItem()
        if item:
            rename_selected_chat(item, self.chats)
            logger.info(f"Renamed chat: {item.text()}")
        else:
            QMessageBox.warning(self, "No Chat Selected", "Please select a chat to rename.")

    def delete_selected_chat(self):
        item = self.chat_history_list.currentItem()
        if item:
            success = delete_selected_chat(item, self.chats)
            if success:
                self.chat_display.setMarkdown("")
                logger.info(f"Deleted chat: {item.text()}")
        else:
            QMessageBox.warning(self, "No Chat Selected", "Please select a chat to delete.")



    def clear_current_chat(self):
        item = self.chat_history_list.currentItem()
        if item:
            clear_chat(item.data(Qt.UserRole), self.chats, self.chat_display)
            logger.info(f"Cleared chat: {item.text()}")
        else:
            QMessageBox.warning(self, "No Chat Selected", "Please select a chat to clear.")

    def switch_chat(self, item):
        chat_id = item.data(Qt.UserRole)
        switch_chat(chat_id, self.chats, self.chat_display)
        logger.info(f"Switched to chat: {item.text()}")
