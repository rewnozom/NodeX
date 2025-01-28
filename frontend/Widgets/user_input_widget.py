from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QHBoxLayout, QPushButton, QSizePolicy, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QEvent, QTimer
from ai_agent.chat_manager.chat_manager import add_to_chat_history, prepare_messages, load_memory
from ai_agent.utils.token_counter import count_tokens_in_string
from ai_agent.threads.worker_thread import WorkerThread
from ai_agent.services.ai_service import AIService
from log.logger import logger
from ai_agent.utils.helpers import insert_file_name, show_file_suggestions

class UserInputWidget(QWidget):
    def __init__(self, parent=None, icons=None):
        super().__init__(parent)
        self.icons = icons
        self.parent = parent
        self.ai_service = AIService(self.parent.config)
        self.current_chat_id = self.parent.current_chat_id
        self.chats = self.parent.chats
        self.current_model_name = self.parent.current_model_name
        self.agent_system_prompt_content = self.parent.agent_system_prompt_content

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Your Message Label and TextEdit
        user_message_label = QLabel("Your Message:")
        user_message_label.setObjectName("userMessageLabel")  # For theming
        self.user_message_textedit = QTextEdit()
        self.user_message_textedit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.user_message_textedit.setObjectName("userMessageTextEdit")  # For theming
        self.user_message_textedit.textChanged.connect(self.update_token_counter)
        self.user_message_textedit.installEventFilter(self)
        layout.addWidget(user_message_label)
        layout.addWidget(self.user_message_textedit)

        # Token Count and Send Button
        bottom_layout = QHBoxLayout()
        self.token_count_label = QLabel("Tokens: 0")
        self.token_count_label.setStyleSheet("font-size: 12px; color: #B0B0B0;")
        self.token_count_label.setObjectName("tokenCountLabel")  # For theming
        bottom_layout.addWidget(self.token_count_label)

        bottom_layout.addStretch()
        self.send_button = QPushButton("Send")
        self.send_button.setIcon(QIcon(self.icons.get('paper_plane', '')))  # Ensure 'paper_plane' icon exists
        self.send_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.send_button.setMinimumWidth(80)
        self.send_button.setObjectName("sendButton")  # For theming

        bottom_layout.addWidget(self.send_button)

        layout.addLayout(bottom_layout)

        # Connect signals
        self.send_button.clicked.connect(self.send_message)

    def send_message(self):
        message = self.user_message_textedit.toPlainText().strip()
        if message:
            # Display the user's message
            self.display_user_message(message)

            # Add the message to the chat history
            add_to_chat_history(self.current_chat_id, self.chats, {'role': 'user', 'content': message})

            # Prepare the messages for the AI model
            system_prompt = self.agent_system_prompt_content
            user_message = message
            memory = load_memory()
            messages = prepare_messages(system_prompt, user_message, self.current_model_name, self.parent.config)

            # Start a worker thread to get AI response
            self.worker_thread = WorkerThread(messages, self.ai_service)
            self.worker_thread.response_ready.connect(self.handle_ai_response)
            self.worker_thread.error_occurred.connect(self.handle_ai_error)
            self.worker_thread.code_blocks_found.connect(self.handle_code_blocks)
            self.worker_thread.start()

            # Clear the user message text edit
            self.user_message_textedit.clear()

    def handle_ai_response(self, response_content, additional_data):
        # Display the AI's message
        self.display_ai_message(response_content)

        # Add the AI's message to the chat history
        add_to_chat_history(self.current_chat_id, self.chats, {'role': 'assistant', 'content': response_content})

        # Save the chat log
        self.parent.save_chat_log(self.current_chat_id, self.chats[self.current_chat_id])

    def handle_ai_error(self, error_message):
        QMessageBox.critical(self, "AI Error", f"An error occurred: {error_message}")
        logger.error(f"AI Error: {error_message}")

    def handle_code_blocks(self, code_blocks):
        for code_block in code_blocks:
            language = code_block['language']
            code = code_block['code']
            logger.info(f"Code block found ({language}): {code}")

    def display_user_message(self, message):
        formatted_message = f"**User:** {message}"
        self.append_markdown(formatted_message)

    def display_ai_message(self, message):
        formatted_message = f"**AI:** {message}"
        self.append_markdown(formatted_message)

    def append_markdown(self, message):
        current_content = self.parent.chat_display.toPlainText()
        new_content = f"{current_content}\n\n{message}"
        self.parent.chat_display.setMarkdown(new_content)

    def update_token_counter(self):
        content = self.user_message_textedit.toPlainText()
        token_count = count_tokens_in_string(content)
        self.token_count_label.setText(f"Tokens: {token_count}")

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress and source is self.user_message_textedit:
            if event.key() == Qt.Key_At:
                QTimer.singleShot(100, self.show_file_suggestions)
                return True
            elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
                modifiers = event.modifiers()
                if modifiers & Qt.ShiftModifier:
                    cursor = self.user_message_textedit.textCursor()
                    cursor.insertText('\n')
                    self.user_message_textedit.setTextCursor(cursor)
                    return True
                else:
                    self.send_message()
                    return True
        return super().eventFilter(source, event)

    def show_file_suggestions(self):
        show_file_suggestions(self.user_message_textedit)

    def insert_file_name(self, file_name):
        insert_file_name(self.user_message_textedit, file_name)
