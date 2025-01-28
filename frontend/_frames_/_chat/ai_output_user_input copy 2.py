# ./frontend/pages/qframes/chat/ai_output_user_input.py



from typing import List, Optional, Union
from PySide6.QtCore import Qt, Signal, QTimer, QEvent, QObject, QPoint
from PySide6.QtGui import QIcon, QTextCursor, QKeyEvent
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QSplitter, QWidget,
    QSizePolicy, QMessageBox, QMenu, QApplication
)

from log.logger import logger
from ai_agent.utils.token_counter import count_tokens_in_string
from ai_agent.utils.helpers import insert_file_name, show_file_suggestions
from Styles.code_block_style import MarkdownRenderer
from Styles.theme_manager import ThemeManager
from Config.AppConfig.icon_config import ICONS

from Config.phone_config.phone_functions import (
    MobileStyles, MobileOptimizations, ChatBubbleDelegate, apply_mobile_style,
    VoiceInputButton  # Om röstinmatning ska inkluderas
)
from frontend._layout.layout_manager import LayoutManager  # Om behövligt

class AIOutputUserInput(QFrame):
    """
    QFrame for AI chat output display and user input components.
    Handles conversation display, user input, and related functionality.
    """
    
    # Define signals
    messageSubmitted = Signal(str)      # When user sends a message
    contentCopied = Signal(str)         # When content is copied
    previewToggled = Signal(bool)       # When markdown preview is toggled
    errorOccurred = Signal(str)         # When an error occurs
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Message history
        self.message_history: List[str] = []
        self.history_index: int = -1
        
        # Draft message auto-save timer
        self.draft_timer: QTimer = QTimer()
        self.draft_timer.setInterval(1000)  # Save draft every second
        self.draft_timer.timeout.connect(self._save_draft)
        
        # Set frame properties
        self.setObjectName("aiOutputUserInputFrame")
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        
        # Layout type
        self.is_phone_layout = self.parent.config.get('enable_phone_layout', False)
        
        # Apply mobile optimizations if in phone layout
        if self.is_phone_layout:
            MobileOptimizations.apply_optimizations(self)
        
        # Initialize UI based on layout type
        if self.is_phone_layout:
            self._init_phone_ui()
        else:
            self._init_desktop_ui()
            
        self._connect_signals()
        self._load_draft()  # Load any saved draft
    
    def _init_phone_ui(self):
        """Initialize phone-optimized UI."""
        # Main vertical layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Chat display takes most of the space
        self.chat_display = MarkdownRenderer()
        self.chat_display.setReadOnly(True)
        self.chat_display.setObjectName("chatDisplay")
        self.chat_display.setContextMenuPolicy(Qt.CustomContextMenu)
        self.chat_display.customContextMenuRequested.connect(self._show_chat_context_menu)
        
        # Apply code block styles
        code_block_styles = ThemeManager.get_theme().get('CODE_BLOCK_STYLE', {})
        self.chat_display.apply_styles(code_block_styles)
        
        # Set up ChatBubbleDelegate for mobile
        self.chat_display.setItemDelegate(ChatBubbleDelegate())
        
        # Apply mobile styles
        MobileStyles.apply_mobile_theme(self.chat_display)
        
        # Create a container for the input area at the bottom
        self.input_container = QWidget()
        self.input_container.setObjectName("mobileInputContainer")
        input_layout = QVBoxLayout(self.input_container)
        input_layout.setContentsMargins(5, 5, 5, 5)
        input_layout.setSpacing(5)
        
        # Message input with expanding height
        self.message_input = QTextEdit()
        self.message_input.setObjectName("mobileMessageInput")
        self.message_input.setMinimumHeight(40)  # Initial height
        self.message_input.setMaximumHeight(120)  # Max height before scrolling
        self.message_input.installEventFilter(self)
        self.message_input.setContextMenuPolicy(Qt.CustomContextMenu)
        self.message_input.customContextMenuRequested.connect(self._show_input_context_menu)
        
        # Apply mobile styles to message_input
        apply_mobile_style(self.message_input, "mobileInput")
        
        # Top button row
        top_button_layout = QHBoxLayout()
        
        # Token counter with smaller font
        self.token_count_label = QLabel("Tokens: 0")
        self.token_count_label.setStyleSheet("font-size: 10px; color: #B0B0B0;")
        self.token_count_label.setObjectName("mobileTokenCountLabel")
        top_button_layout.addWidget(self.token_count_label)
        
        top_button_layout.addStretch()
        
        # Compact buttons with icons only
        self.preview_button = QPushButton()
        self.preview_button.setIcon(QIcon(ICONS.get('preview', '')))
        self.preview_button.setToolTip("Preview")
        self.preview_button.setCheckable(True)
        self.preview_button.setMinimumSize(40, 40)  # Touch-friendly size
        self.preview_button.setObjectName("mobileActionButton")
        apply_mobile_style(self.preview_button, "mobileActionButton")
        
        self.copy_button = QPushButton()
        self.copy_button.setIcon(QIcon(ICONS.get('copy', '')))
        self.copy_button.setToolTip("Copy")
        self.copy_button.setMinimumSize(40, 40)
        self.copy_button.setObjectName("mobileActionButton")
        apply_mobile_style(self.copy_button, "mobileActionButton")
        
        self.clear_button = QPushButton()
        self.clear_button.setIcon(QIcon(ICONS.get('clear', '')))
        self.clear_button.setToolTip("Clear")
        self.clear_button.setMinimumSize(40, 40)
        self.clear_button.setObjectName("mobileActionButton")
        apply_mobile_style(self.clear_button, "mobileActionButton")
        
        top_button_layout.addWidget(self.preview_button)
        top_button_layout.addWidget(self.copy_button)
        top_button_layout.addWidget(self.clear_button)
        
        # Input area with send button
        input_row_layout = QHBoxLayout()
        input_row_layout.addWidget(self.message_input)
        
        self.send_button = QPushButton()
        self.send_button.setIcon(QIcon(ICONS.get('paper_plane', '')))
        self.send_button.setToolTip("Send")
        self.send_button.setMinimumSize(50, 50)  # Larger send button
        self.send_button.setObjectName("mobileSendButton")
        apply_mobile_style(self.send_button, "mobileSendButton")
        input_row_layout.addWidget(self.send_button)
        
        # Add layouts to input container
        input_layout.addLayout(top_button_layout)
        input_layout.addLayout(input_row_layout)
        
        # Add layouts to main layout
        layout.addWidget(self.chat_display, stretch=1)  # Chat takes remaining space
        layout.addWidget(self.input_container)
        
        # Style the input container
        self.input_container.setStyleSheet("""
            QWidget#mobileInputContainer {
                background-color: rgba(0, 0, 0, 0.05);
                border-top: 1px solid rgba(0, 0, 0, 0.1);
            }
            QPushButton#mobileActionButton {
                background: transparent;
                border: none;
                padding: 8px;
                border-radius: 20px;
            }
            QPushButton#mobileActionButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
            QPushButton#mobileSendButton {
                background-color: #2196F3;
                border: none;
                border-radius: 25px;
                padding: 12px;
            }
            QPushButton#mobileSendButton:hover {
                background-color: #1976D2;
            }
            QTextEdit#mobileMessageInput {
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 20px;
                padding: 8px 12px;
                background-color: white;
            }
        """)
    
    def _init_desktop_ui(self):
        """Initialize desktop UI."""
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
        
        # Add context menu
        self.chat_display.setContextMenuPolicy(Qt.CustomContextMenu)
        self.chat_display.customContextMenuRequested.connect(self._show_chat_context_menu)
        
        # Apply code block styles
        code_block_styles = ThemeManager.get_theme().get('CODE_BLOCK_STYLE', {})
        self.chat_display.apply_styles(code_block_styles)
        
        # Set up ChatBubbleDelegate
        self.chat_display.setItemDelegate(ChatBubbleDelegate())
        
        # Apply mobile styles if in phone layout
        if self.is_phone_layout:
            MobileStyles.apply_mobile_theme(self.chat_display)
    
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
        
        # Add context menu
        self.message_input.setContextMenuPolicy(Qt.CustomContextMenu)
        self.message_input.customContextMenuRequested.connect(self._show_input_context_menu)
        
        layout.addWidget(self.message_input)
        
        # Bottom row with controls
        bottom_layout = QHBoxLayout()
        
        # Token counter
        self.token_count_label = QLabel("Tokens: 0")
        self.token_count_label.setStyleSheet("font-size: 12px; color: #B0B0B0;")
        self.token_count_label.setObjectName("tokenCountLabel")
        bottom_layout.addWidget(self.token_count_label)
        
        bottom_layout.addStretch()
        
        # Preview button
        self.preview_button = QPushButton("Preview")
        self.preview_button.setIcon(QIcon(ICONS.get('preview', '')))
        self.preview_button.setCheckable(True)
        self.preview_button.setObjectName("previewButton")
        
        # Copy button
        self.copy_button = QPushButton("Copy")
        self.copy_button.setIcon(QIcon(ICONS.get('copy', '')))
        self.copy_button.setObjectName("copyButton")
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setIcon(QIcon(ICONS.get('clear', '')))
        self.clear_button.setObjectName("clearButton")
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.setIcon(QIcon(ICONS.get('paper_plane', '')))
        self.send_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.send_button.setMinimumWidth(80)
        self.send_button.setObjectName("sendButton")
        
        # Add buttons to bottom layout
        bottom_layout.addWidget(self.preview_button)
        bottom_layout.addWidget(self.copy_button)
        bottom_layout.addWidget(self.clear_button)
        bottom_layout.addWidget(self.send_button)
        
        layout.addLayout(bottom_layout)
        
        # Apply mobile styles if in phone layout
        if self.is_phone_layout:
            MobileStyles.apply_mobile_theme(self.user_input_widget)
            apply_mobile_style(message_label, "mobileSubheader")
            apply_mobile_style(self.message_input, "mobileInput")
            apply_mobile_style(self.preview_button, "mobileActionButton")
            apply_mobile_style(self.copy_button, "mobileActionButton")
            apply_mobile_style(self.clear_button, "mobileActionButton")
            apply_mobile_style(self.send_button, "mobileSendButton")
    
    def _connect_signals(self):
        """Connect all signals to their respective slots."""
        # Button signals
        self.send_button.clicked.connect(self._handle_send)
        self.preview_button.toggled.connect(self._toggle_preview)
        self.copy_button.clicked.connect(self._copy_content)
        self.clear_button.clicked.connect(self._clear_input)
        
        # Text change signals
        self.message_input.textChanged.connect(self._update_token_count)
        self.message_input.textChanged.connect(self._handle_text_changed)
        
        # Start draft timer
        self.draft_timer.start()
    
    def _show_chat_context_menu(self, position: QPoint):
        """Show context menu for chat display."""
        try:
            menu = QMenu(self)
            
            # Add actions
            copy_action = menu.addAction(QIcon(ICONS.get('copy', '')), "Copy")
            select_all_action = menu.addAction(QIcon(ICONS.get('select_all', '')), "Select All")
            clear_action = menu.addAction(QIcon(ICONS.get('clear', '')), "Clear Chat")
            
            # Execute menu and handle result
            action = menu.exec_(self.chat_display.mapToGlobal(position))
            
            if action == copy_action:
                self._copy_content()
            elif action == select_all_action:
                self.chat_display.selectAll()
            elif action == clear_action:
                self.clear_chat()
                
        except Exception as e:
            self._handle_error(f"Context menu error: {str(e)}")
    
    def _show_input_context_menu(self, position: QPoint):
        """Show context menu for message input."""
        try:
            menu = QMenu(self)
            
            # Add actions
            undo_action = menu.addAction(QIcon(ICONS.get('undo', '')), "Undo")
            redo_action = menu.addAction(QIcon(ICONS.get('redo', '')), "Redo")
            menu.addSeparator()
            cut_action = menu.addAction(QIcon(ICONS.get('cut', '')), "Cut")
            copy_action = menu.addAction(QIcon(ICONS.get('copy', '')), "Copy")
            paste_action = menu.addAction(QIcon(ICONS.get('paste', '')), "Paste")
            menu.addSeparator()
            select_all_action = menu.addAction(QIcon(ICONS.get('select_all', '')), "Select All")
            clear_action = menu.addAction(QIcon(ICONS.get('clear', '')), "Clear")
            
            # Enable/disable actions based on state
            undo_action.setEnabled(self.message_input.document().isUndoAvailable())
            redo_action.setEnabled(self.message_input.document().isRedoAvailable())
            has_selection = self.message_input.textCursor().hasSelection()
            cut_action.setEnabled(has_selection)
            copy_action.setEnabled(has_selection)
            paste_action.setEnabled(QApplication.clipboard().text() != '')
            
            # Execute menu and handle result
            action = menu.exec_(self.message_input.mapToGlobal(position))
            
            if action == undo_action:
                self.message_input.undo()
            elif action == redo_action:
                self.message_input.redo()
            elif action == cut_action:
                self.message_input.cut()
            elif action == copy_action:
                self.message_input.copy()
            elif action == paste_action:
                self.message_input.paste()
            elif action == select_all_action:
                self.message_input.selectAll()
            elif action == clear_action:
                self._clear_input()
                
        except Exception as e:
            self._handle_error(f"Context menu error: {str(e)}")
    
    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        """Enhanced event filter with error handling and history navigation."""
        try:
            if event.type() == QEvent.KeyPress and source is self.message_input:
                key_event = QKeyEvent(event)
                
                # File suggestions
                if key_event.key() == Qt.Key_At:
                    QTimer.singleShot(100, self._show_file_suggestions)
                    return True
                
                # Message history navigation
                elif key_event.key() == Qt.Key_Up and key_event.modifiers() == Qt.ControlModifier:
                    self._navigate_history(direction="up")
                    return True
                elif key_event.key() == Qt.Key_Down and key_event.modifiers() == Qt.ControlModifier:
                    self._navigate_history(direction="down")
                    return True
                
                # Send or newline
                elif key_event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    if key_event.modifiers() & Qt.ShiftModifier:
                        cursor = self.message_input.textCursor()
                        cursor.insertText('\n')
                        return True
                    else:
                        self._handle_send()
                        return True
            
            return super().eventFilter(source, event)
            
        except Exception as e:
            self._handle_error(f"Event handling error: {str(e)}")
            return False
    
    def _handle_send(self):
        """Enhanced message sending with history and error handling."""
        try:
            message = self.message_input.toPlainText().strip()
            if message:
                self.messageSubmitted.emit(message)
                self.message_history.append(message)
                self.history_index = len(self.message_history)
                self.message_input.clear()
                self._clear_draft()
                self.draft_timer.stop()
        except Exception as e:
            self._handle_error(f"Error sending message: {str(e)}")
    
    def _navigate_history(self, direction: str):
        """Navigate through message history."""
        try:
            if not self.message_history:
                return
                
            if direction == "up" and self.history_index > 0:
                self.history_index -= 1
            elif direction == "down" and self.history_index < len(self.message_history):
                self.history_index += 1
                
            if 0 <= self.history_index < len(self.message_history):
                self.set_message(self.message_history[self.history_index])
            elif self.history_index == len(self.message_history):
                self.message_input.clear()
        except Exception as e:
            self._handle_error(f"History navigation error: {str(e)}")
    
    def _handle_text_changed(self):
        """Handle text changes in message input."""
        if not self.draft_timer.isActive():
            self.draft_timer.start()
    
    def _toggle_preview(self, enabled: bool):
        """Toggle markdown preview."""
        try:
            if enabled:
                preview_text = self.message_input.toPlainText()
                self.message_input.setReadOnly(True)
                self.message_input.setMarkdown(preview_text)
            else:
                original_text = self.message_input.toPlainText()
                self.message_input.setReadOnly(False)
                self.message_input.setPlainText(original_text)
                
            self.previewToggled.emit(enabled)
            
        except Exception as e:
            self._handle_error(f"Preview error: {str(e)}")
            self.preview_button.setChecked(False)
    
    def _copy_content(self):
        """Copy content to clipboard."""
        try:
            content = self.chat_display.toPlainText()
            if content:
                QApplication.clipboard().setText(content)
                self.contentCopied.emit(content)
        except Exception as e:
            self._handle_error(f"Copy error: {str(e)}")
    
    def _clear_input(self):
        """Clear the message input."""
        try:
            self.message_input.clear()
            self._clear_draft()
            self.draft_timer.stop()
        except Exception as e:
            self._handle_error(f"Clear input error: {str(e)}")
    
    def _update_token_count(self):
        """Update the token counter."""
        try:
            content = self.message_input.toPlainText()
            token_count = count_tokens_in_string(content)
            self.token_count_label.setText(f"Tokens: {token_count}")
        except Exception as e:
            logger.error(f"Token count error: {str(e)}")
            self.token_count_label.setText("Tokens: ???")
    
    def _show_file_suggestions(self):
        """Show file suggestions when @ is typed."""
        try:
            show_file_suggestions(self.message_input)
        except Exception as e:
            self._handle_error(f"File suggestions error: {str(e)}")
    
    def _save_draft(self):
        """Auto-save draft message."""
        try:
            draft = self.message_input.toPlainText()
            if draft:
                self.parent.config.save_draft_message(draft)
        except Exception as e:
            logger.error(f"Error saving draft: {str(e)}")
    
    def _load_draft(self):
        """Load saved draft message."""
        try:
            draft = self.parent.config.load_draft_message()
            if draft:
                self.set_message(draft)
                self.draft_timer.start()
        except Exception as e:
            logger.error(f"Error loading draft: {str(e)}")
    
    def _clear_draft(self):
        """Clear saved draft message."""
        try:
            self.parent.config.clear_draft_message()
            self.draft_timer.stop()
        except Exception as e:
            logger.error(f"Error clearing draft: {str(e)}")
    
    def _handle_error(self, error_msg: str):
        """Handle errors uniformly."""
        logger.error(error_msg)
        self.errorOccurred.emit(error_msg)
        QMessageBox.critical(self, "Error", error_msg)
    
    # Public methods for external access
    def display_user_message(self, message: str):
        """Display a user message in the chat."""
        try:
            formatted_message = f"**User:** {message}"
            self._append_to_chat(formatted_message)
        except Exception as e:
            self._handle_error(f"Error displaying user message: {str(e)}")
    
    def display_ai_message(self, message: str):
        """Display an AI message in the chat."""
        try:
            formatted_message = f"**AI:** {message}"
            self._append_to_chat(formatted_message)
        except Exception as e:
            self._handle_error(f"Error displaying AI message: {str(e)}")
    
    def _append_to_chat(self, message: str):
        """Append a message to the chat display."""
        try:
            current_content = self.chat_display.toPlainText()
            new_content = f"{current_content}\n\n{message}" if current_content else message
            self.chat_display.setMarkdown(new_content)
            
            # Scroll to bottom
            scrollbar = self.chat_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            self._handle_error(f"Error appending to chat: {str(e)}")
    
    def clear_chat(self):
        """Clear the chat display."""
        try:
            self.chat_display.clear()
            self.message_history.clear()
            self.history_index = -1
        except Exception as e:
            self._handle_error(f"Error clearing chat: {str(e)}")
    
    def get_current_message(self) -> str:
        """Get the current message in the input field."""
        return self.message_input.toPlainText()
    
    def set_message(self, message: str):
        """Set the message in the input field."""
        try:
            self.message_input.setPlainText(message)
            cursor = self.message_input.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.message_input.setTextCursor(cursor)
        except Exception as e:
            self._handle_error(f"Error setting message: {str(e)}")
    
    def focus_input(self):
        """Set focus to the message input."""
        self.message_input.setFocus()
    
    def get_chat_content(self) -> str:
        """Get all chat content."""
        return self.chat_display.toPlainText()
    
    def get_splitter_sizes(self) -> List[int]:
        """Get the current splitter sizes."""
        return self.main_splitter.sizes()
    
    def set_splitter_sizes(self, sizes: List[int]):
        """Set the splitter sizes."""
        try:
            self.main_splitter.setSizes(sizes)
        except Exception as e:
            self._handle_error(f"Error setting splitter sizes: {str(e)}")
    
    def load_chat_history(self, messages: List[dict]):
        """Load chat history from messages."""
        try:
            self.clear_chat()
            for message in messages:
                if message['role'] == 'user':
                    self.display_user_message(message['content'])
                else:
                    self.display_ai_message(message['content'])
        except Exception as e:
            self._handle_error(f"Error loading chat history: {str(e)}")
    
    def enable_input(self, enabled: bool = True):
        """Enable or disable input controls."""
        try:
            self.message_input.setEnabled(enabled)
            self.send_button.setEnabled(enabled)
            self.preview_button.setEnabled(enabled)
            if not enabled:
                self.preview_button.setChecked(False)
        except Exception as e:
            self._handle_error(f"Error {'enabling' if enabled else 'disabling'} input: {str(e)}")
