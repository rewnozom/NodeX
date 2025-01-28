# ./frontend/pages/qframes/chat/ai_output_user_input.py

from PySide6.QtCore import Qt, Signal, QTimer, QEvent
from PySide6.QtGui import QIcon, QTextCursor
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QSplitter, QWidget,
    QSizePolicy
)

from ai_agent.utils.token_counter import count_tokens_in_string
from ai_agent.utils.helpers import insert_file_name, show_file_suggestions
from Styles.code_block_style import MarkdownRenderer
from Styles.theme_manager import ThemeManager
from Config.AppConfig.icon_config import ICONS

class AIOutputUserInput(QFrame):
    """
    A QFrame that contains both the AI chat output display and user input components.
    Handles the display of conversations, user input, and related functionality.
    """
    
    # Define signals
    messageSubmitted = Signal(str)  # Emitted when user sends a message
    
    def __init__(self, parent=None):
        """Initialize the output/input frame."""
        super().__init__(parent)
        self.parent = parent
        
        # Set frame properties
        self.setObjectName("aiOutputUserInputFrame")
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """Initialize the UI components."""
        # Main vertical layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create main splitter for resizable areas
        self.main_splitter = QSplitter(Qt.Vertical)
        
        # Initialize chat display
        self._init_chat_display()
        
        # Initialize user input area
        self._init_user_input()
        
        # Add components to splitter
        self.main_splitter.addWidget(self.chat_display)
        self.main_splitter.addWidget(self.user_input_widget)
        
        # Set initial sizes (3:1 ratio)
        self.main_splitter.setStretchFactor(0, 3)  # Chat display
        self.main_splitter.setStretchFactor(1, 1)  # User input
        
        layout.addWidget(self.main_splitter)
    
    def _init_chat_display(self):
        """Initialize the chat display area."""
        self.chat_display = MarkdownRenderer()
        self.chat_display.setReadOnly(True)
        self.chat_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.chat_display.setObjectName("chatDisplay")
        
        # Apply code block styles
        code_block_styles = ThemeManager.get_theme().get('CODE_BLOCK_STYLE', {})
        self.chat_display.apply_styles(code_block_styles)
    
    def _init_user_input(self):
        """Initialize the user input area."""
        self.user_input_widget = QWidget()
        self.user_input_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.user_input_widget.setObjectName("userInputWidget")
        
        layout = QVBoxLayout(self.user_input_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Message Label
        message_label = QLabel("Your Message:")
        message_label.setObjectName("userMessageLabel")
        layout.addWidget(message_label)
        
        # Message Input
        self.message_input = QTextEdit()
        self.message_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.message_input.setObjectName("messageInput")
        self.message_input.installEventFilter(self)  # For custom key handling
        layout.addWidget(self.message_input)
        
        # Bottom row with token count and send button
        bottom_layout = QHBoxLayout()
        
        # Token counter
        self.token_count_label = QLabel("Tokens: 0")
        self.token_count_label.setStyleSheet("font-size: 12px; color: #B0B0B0;")
        self.token_count_label.setObjectName("tokenCountLabel")
        bottom_layout.addWidget(self.token_count_label)
        
        bottom_layout.addStretch()
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.setIcon(QIcon(ICONS.get('paper_plane', '')))
        self.send_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.send_button.setMinimumWidth(80)
        self.send_button.setObjectName("sendButton")
        bottom_layout.addWidget(self.send_button)
        
        layout.addLayout(bottom_layout)
    
    def _connect_signals(self):
        """Connect all signals to their respective slots."""
        self.send_button.clicked.connect(self._handle_send)
        self.message_input.textChanged.connect(self._update_token_count)
    
    def eventFilter(self, source, event):
        """
        Handle custom key events for the message input.
        - Enter -> Send message
        - Shift+Enter -> New line
        - @ -> Show file suggestions
        """
        if event.type() == QEvent.KeyPress and source is self.message_input:
            if event.key() == Qt.Key_At:
                # Show file suggestions after a brief delay
                QTimer.singleShot(100, self._show_file_suggestions)
                return True
            
            elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
                modifiers = event.modifiers()
                if modifiers & Qt.ShiftModifier:
                    # Insert new line with Shift+Enter
                    cursor = self.message_input.textCursor()
                    cursor.insertText('\n')
                    return True
                else:
                    # Send message with Enter
                    self._handle_send()
                    return True
        
        return super().eventFilter(source, event)
    
    def _handle_send(self):
        """Handle sending the message."""
        message = self.message_input.toPlainText().strip()
        if message:
            self.messageSubmitted.emit(message)
            self.message_input.clear()
    
    def _update_token_count(self):
        """Update the token counter."""
        content = self.message_input.toPlainText()
        token_count = count_tokens_in_string(content)
        self.token_count_label.setText(f"Tokens: {token_count}")
    
    def _show_file_suggestions(self):
        """Show file suggestions when @ is typed."""
        show_file_suggestions(self.message_input)
    
    # Public methods
    def display_user_message(self, message):
        """Display a user message in the chat."""
        formatted_message = f"**User:** {message}"
        self._append_to_chat(formatted_message)
    
    def display_ai_message(self, message):
        """Display an AI message in the chat."""
        formatted_message = f"**AI:** {message}"
        self._append_to_chat(formatted_message)
    
    def _append_to_chat(self, message):
        """Append a message to the chat display."""
        current_content = self.chat_display.toPlainText()
        new_content = f"{current_content}\n\n{message}" if current_content else message
        self.chat_display.setMarkdown(new_content)
        
        # Scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_chat(self):
        """Clear the chat display."""
        self.chat_display.clear()
    
    def get_current_message(self):
        """Get the current message in the input field."""
        return self.message_input.toPlainText()
    
    def set_message(self, message):
        """Set the message in the input field."""
        self.message_input.setPlainText(message)
    
    def focus_input(self):
        """Set focus to the message input."""
        self.message_input.setFocus()
    
    def update_theme(self):
        """Update the theme of the chat display."""
        code_block_styles = ThemeManager.get_theme().get('CODE_BLOCK_STYLE', {})
        self.chat_display.apply_styles(code_block_styles)
    
    def get_splitter_sizes(self):
        """Get the current splitter sizes."""
        return self.main_splitter.sizes()
    
    def set_splitter_sizes(self, sizes):
        """Set the splitter sizes."""
        self.main_splitter.setSizes(sizes)