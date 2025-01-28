
# -*- coding: utf-8 -*-
# ./frontend/pages/desktop/Layout/chat.py

import os
import threading
from datetime import datetime
import re  # Added for regex operations

import markdown  # For Markdown rendering
from PySide6.QtCore import Qt, QTimer, QEvent, QThread, Slot, Signal, QObject
from PySide6.QtGui import QIcon, QAction, QTextCursor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel,
    QListWidget, QFileDialog, QMessageBox, QComboBox, QCheckBox,
    QDoubleSpinBox, QSlider, QSpinBox, QSplitter, QTextBrowser,
    QSizePolicy, QProgressDialog, QLineEdit, QListWidgetItem, QFrame, QProgressBar, QTabWidget, QScrollArea, QApplication
)
from pygments.styles import STYLE_MAP  # For registering custom styles

# Import backend modules
from ai_agent.models.models import MODELS, get_model
from ai_agent.chat_manager.chat_manager import (
    load_chat_history, start_new_chat, switch_chat,
    rename_selected_chat, delete_selected_chat, save_chat_log, add_to_chat_history,
    prepare_messages, upload_file, view_files
)
from ai_agent.config.ai_config import Config
from ai_agent.memory.memory_manager import load_memory
from ai_agent.config.prompt_manager import (
    load_specific_system_prompt, save_system_prompt, load_all_system_prompts
)

from ai_agent.threads.worker_thread import WorkerThread
from ai_agent.services.ai_service import AIService
from ai_agent.utils.helpers import insert_file_name, show_file_suggestions
from Utils.llm_util.llm_sorted_func import process_files  # Import the utility module

from log.logger import logger
from Config.AppConfig.icon_config import ICONS
from Styles.theme_manager import apply_theme, ThemeManager
from Styles.code_block_style import MarkdownRenderer  # For code block styling

# -------------------------------------------------------------------
# Initialize the configuration (now combined from agent and general settings)
# -------------------------------------------------------------------
config = Config()


# ------------------- WorkerSignals Class ------------------- #

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    finished = Signal()
    error = Signal(str)
    result = Signal(object)
    progress = Signal(str, str)


# ------------------- Worker Class ------------------- #

class Worker(QObject):
    """
    Worker class to handle processing of Markdown files in a separate thread.
    """
    progress_update = Signal(str, str)  # (Item Name, Status)
    processing_finished = Signal()

    def __init__(self, input_dir, output_dir, system_prompt, llm):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.system_prompt = system_prompt
        self.llm = llm
        self._is_running = True  # Flag to control the worker's running state
        logger.debug("Worker initialized with input_dir='%s', output_dir='%s'", input_dir, output_dir)

    def run(self):
        """
        Run the file processing.
        """
        logger.debug("Worker thread started processing files.")
        process_files(
            input_dir=self.input_dir,
            output_dir=self.output_dir,
            system_prompt=self.system_prompt,
            llm=self.llm,
            progress_callback=self.emit_progress,
            is_running=lambda: self._is_running  # Pass the running flag as a callable
        )
        logger.debug("Worker thread finished processing files.")
        self.processing_finished.emit()

    def emit_progress(self, item_name, status):
        """
        Emit progress updates to the main thread.
        """
        logger.debug("Processing '%s' with status '%s'", item_name, status)
        self.progress_update.emit(item_name, status)

    def stop(self):
        """
        Stop the worker gracefully.
        """
        logger.info("Worker stop requested.")
        self._is_running = False


# ------------------- Token Counting Functions ------------------- #
import tiktoken

def count_tokens_in_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Return the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(string))

def count_tokens_in_messages(messages, encoding_name: str = "cl100k_base") -> int:
    """Return the number of tokens used by a list of messages."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = 0
    tokens_per_message = 3
    tokens_per_name = 1

    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # Every reply is primed with assistant
    return num_tokens


# ------------------- Code Display Logic Integrated ------------------- #

class CodeDisplayWindow(QWidget):
    """
    Window to display code blocks in a separate, styled window.
    """
    instances = []  # Class-level list to keep references

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
        # Keep a reference to prevent garbage collection
        CodeDisplayWindow.instances.append(code_window)
        logger.info("Code window displayed successfully.")
    except Exception as e:
        logger.error(f"Unexpected error showing code window: {e}")


# ------------------- Page Class ------------------- #
class Page(QWidget):
    """
    Chat Page Class

    This class provides a chat interface, integrating all backend functionalities
    into a PySide6-based GUI.
    """

    def __init__(self, parent=None):
        """
        Initialize the Chat Page.

        Args:
            parent (QWidget): The parent widget, typically the main window.
        """
        super().__init__(parent)
        self.parent = parent  # Reference to the main window
        self.config = config
        self.temperature = self.config.CHAT_TEMPERATURE
        self.max_tokens = self.config.MAX_TOKENS  # Ensure Config has MAX_TOKENS attribute
        self.agent_system_prompt_content = ""  # Initialize the attribute
        self.uploaded_files = []  # List to keep track of uploaded files

        # Initialize variables
        self.chats = {}       # Store chat histories
        self.current_chat_id = None

        # Initialize the AI service
        self.ai_service = AIService(self.config)
        logger.debug("AIService initialized in Chat Page.")

        # Initialize chat history content for display
        self.chat_history_content = []

        # Set up the user interface
        logger.debug("Initializing UI components.")
        self.init_ui()

        # Initialize current_model_name
        self.current_model_name = self.config.CHAT_MODEL
        logger.debug("Current model set to '%s'.", self.current_model_name)

        # Initialize the first chat after UI components are set
        self.start_new_chat()

    def init_ui(self):
        """
        Set up the user interface.
        """
        logger.debug("Setting up the UI.")
        # Apply the current theme to this widget
        theme = self.parent.config['theme'] if self.parent and hasattr(self.parent, 'config') else 'dark'
        apply_theme(self, theme)
        logger.debug("Theme '%s' applied to Chat Page.", theme)

        # Main vertical layout to hold main content and status bar
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Create horizontal layout for main content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(5)

        # Create main splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        logger.debug("Main splitter initialized.")

        # Initialize left sidebar with tabs
        self.init_left_sidebar()

        # Initialize main content
        self.init_main_content()

        # Initialize right sidebar
        self.init_right_sidebar()

        # Add widgets to main splitter
        self.main_splitter.addWidget(self.left_sidebar)
        self.main_splitter.addWidget(self.main_content) 
        self.main_splitter.addWidget(self.right_sidebar)
        logger.debug("Left sidebar, main content, and right sidebar added to splitter.")

        # Set max width for left sidebar (history_tab)
        self.left_sidebar.setMaximumWidth(300)  # Max width for the history tab
        self.left_sidebar.setMinimumWidth(150)  # Minimum width for usability
        logger.debug("Left sidebar width set to min: 150, max: 300.")

        # Set stretch factors to prioritize the main content
        self.main_splitter.setStretchFactor(0, 1)  # Left sidebar
        self.main_splitter.setStretchFactor(1, 4)  # Main content
        self.main_splitter.setStretchFactor(2, 1)  # Right sidebar
        logger.debug("Stretch factors set for splitter.")

        # Allow the splitter to be collapsible
        self.main_splitter.setSizes([200, 600, 200])
        logger.debug("Initial splitter sizes set.")

        content_layout.addWidget(self.main_splitter)
        # Add content_layout with stretch factor 1 to allow it to expand vertically
        main_layout.addLayout(content_layout, 1)

        # Add status bar at the bottom with stretch factor 0
        self.status_bar = QWidget()
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(5, 2, 5, 2)
        status_layout.setSpacing(5)
        
        # Status icon and label
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(16, 16)  # Keeping icon size fixed for consistency
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        
        # Agent status
        self.agent_status_label = QLabel("Developer Agent: Disabled | Crew Agent: Disabled")
        self.agent_status_label.setObjectName("agentStatusLabel")
        
        # Add widgets to status bar
        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.agent_status_label)
        
        # Add status bar to main layout with stretch factor 0
        main_layout.addWidget(self.status_bar, 0)

        # Force update and repaint
        self.update()
        self.repaint()
        logger.debug("UI initialization complete.")

    def init_left_sidebar(self):
        """
        Initialize the left sidebar with tabs.
        """
        logger.debug("Initializing left sidebar with tabs.")
        self.left_sidebar = QTabWidget()
        self.left_sidebar.setTabPosition(QTabWidget.West)
        self.left_sidebar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # Chat History Tab
        self.init_chat_history_tab()
        # File Management Tab
        self.init_file_management_tab()
        # Processing Tab
        self.init_processing_tab()
        # Code Blocks Tab
        self.init_code_blocks_tab()

        # Add tabs to left sidebar
        self.left_sidebar.addTab(self.chat_history_tab, "Chats")
        self.left_sidebar.addTab(self.file_management_tab, "Files")
        self.left_sidebar.addTab(self.processing_tab, "Processing")
        self.left_sidebar.addTab(self.code_blocks_tab, "Code Blocks")
        logger.debug("Tabs added to left sidebar.")

    def init_chat_history_tab(self):
        """
        Initialize the Chat History tab in the left sidebar.
        """
        logger.debug("Initializing Chat History tab.")
        self.chat_history_tab = QWidget()
        
        # Add a scroll area for responsiveness
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Wrapper-widget for scroll content
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        scroll_layout.setSpacing(5)

        # Chat History Title
        chat_history_title = QLabel("Chat History")
        chat_history_title.setAlignment(Qt.AlignCenter)
        chat_history_title.setObjectName("chatHistoryTitle")  # For theming
        scroll_layout.addWidget(chat_history_title)

        # Chat History List
        self.chat_history_list = QListWidget()
        self.chat_history_list.setObjectName("chatHistoryList")  # For theming
        self.chat_history_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll_layout.addWidget(self.chat_history_list)

        # Chat History Buttons Layout
        buttons_layout = QVBoxLayout()  # Vertical layout for buttons
        buttons_layout.setSpacing(5)
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.load_chat_button = QPushButton("Load Chat")
        self.new_chat_button = QPushButton("New Chat")
        self.rename_chat_button = QPushButton("Rename Chat")
        self.delete_chat_button = QPushButton("Delete Chat")
        self.clear_chat_button = QPushButton("Clear Chat")

        # Make buttons larger and more readable
        for button in [self.load_chat_button, self.new_chat_button, self.rename_chat_button, self.delete_chat_button, self.clear_chat_button]:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setMinimumHeight(30)  # Set a minimum height for readability
            buttons_layout.addWidget(button)

        scroll_layout.addLayout(buttons_layout)
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)

        # Add scroll area to tab
        layout = QVBoxLayout(self.chat_history_tab)
        layout.addWidget(scroll_area)

        # Connect buttons' signals
        self.new_chat_button.clicked.connect(self.start_new_chat)
        self.load_chat_button.clicked.connect(self.load_selected_chat)
        self.rename_chat_button.clicked.connect(self.rename_selected_chat)
        self.delete_chat_button.clicked.connect(self.delete_selected_chat)
        self.clear_chat_button.clicked.connect(self.clear_chat)
        self.chat_history_list.itemClicked.connect(self.switch_chat)

        # Load chat history
        self.load_chat_history()
        logger.debug("Chat History tab initialized.")

    def init_file_management_tab(self):
        """
        Initialize the File Management tab in the left sidebar.
        """
        logger.debug("Initializing File Management tab.")
        self.file_management_tab = QWidget()
        layout = QVBoxLayout(self.file_management_tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # File Management Title
        file_management_title = QLabel("File Management")
        file_management_title.setAlignment(Qt.AlignCenter)
        file_management_title.setObjectName("fileManagementTitle")  # For theming
        layout.addWidget(file_management_title)

        # File Upload and View Buttons Layout
        buttons_layout = QHBoxLayout()
        self.upload_file_button = QPushButton("Upload")
        self.view_files_button = QPushButton("View")
        buttons_layout.addWidget(self.upload_file_button)
        buttons_layout.addWidget(self.view_files_button)
        layout.addLayout(buttons_layout)

        # Connect signals
        self.upload_file_button.clicked.connect(self.upload_file)
        self.view_files_button.clicked.connect(self.view_files)

        # Add stretch to push buttons to the top
        layout.addStretch()
        logger.debug("File Management tab initialized.")

    def init_processing_tab(self):
        """
        Initialize the Processing tab in the left sidebar.
        """
        logger.debug("Initializing Processing tab.")
        self.processing_tab = QWidget()
        layout = QVBoxLayout(self.processing_tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Process Markdown Files Button
        self.start_processing_button = QPushButton("Process Files")
        self.start_processing_button.setObjectName("startProcessingButton")  # For theming
        layout.addWidget(self.start_processing_button)
        self.start_processing_button.clicked.connect(self.start_code_analysis)
        logger.debug("Process Files button added.")

        # Stop Button Below the Process Button
        self.stop_processing_button = QPushButton("Stop")
        self.stop_processing_button.setObjectName("stopProcessingButton")  # For theming
        self.stop_processing_button.setEnabled(False)  # Initially disabled
        layout.addWidget(self.stop_processing_button)
        self.stop_processing_button.clicked.connect(self.stop_processing_files)
        logger.debug("Stop button added and disabled initially.")

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setObjectName("processingProgressBar")  # For theming
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.progress_bar)
        logger.debug("Progress bar added and hidden initially.")

        # Processing Log
        self.processing_log = QTextEdit()
        self.processing_log.setReadOnly(True)
        self.processing_log.setVisible(False)
        self.processing_log.setObjectName("processingLog")  # For theming
        self.processing_log.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.processing_log)
        logger.debug("Processing log added and hidden initially.")

        # Add stretch to push widgets to the top
        layout.addStretch()
        logger.debug("Processing tab initialized.")

    def init_code_blocks_tab(self):
        """
        Initialize the Code Blocks tab in the left sidebar.
        """
        logger.debug("Initializing Code Blocks tab.")
        self.code_blocks_tab = QWidget()
        
        # Add a scroll area for responsiveness
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Wrapper-widget for scroll content
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        scroll_layout.setSpacing(5)

        # Code Blocks Title
        code_blocks_title = QLabel("Code Blocks")
        code_blocks_title.setAlignment(Qt.AlignCenter)
        code_blocks_title.setObjectName("codeBlocksTitle")  # For theming
        scroll_layout.addWidget(code_blocks_title)

        # Code Blocks List
        self.code_blocks_list = QListWidget()
        self.code_blocks_list.setObjectName("codeBlocksList")  # For theming
        self.code_blocks_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll_layout.addWidget(self.code_blocks_list)

        # Connect double-click signal to open code block
        self.code_blocks_list.itemDoubleClicked.connect(self.open_code_block)

        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)

        # Add scroll area to tab
        layout = QVBoxLayout(self.code_blocks_tab)
        layout.addWidget(scroll_area)

        logger.debug("Code Blocks tab initialized.")

    def init_main_content(self):
        """
        Initialize the main chat content area.
        """
        logger.debug("Initializing main content area.")
        self.main_content = QWidget()
        layout = QVBoxLayout(self.main_content)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Chat Display
        self.chat_display = MarkdownRenderer()
        self.chat_display.setObjectName("chatDisplay")  # For theming
        self.chat_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.chat_display)
        logger.debug("Chat display added.")

        # User Message Input Layout
        input_layout = QHBoxLayout()
        input_layout.setSpacing(5)

        # User Message TextEdit
        self.user_message_textedit = QTextEdit()
        self.user_message_textedit.setPlaceholderText("Type your message here...")
        self.user_message_textedit.setFixedHeight(60)
        self.user_message_textedit.setObjectName("userMessageTextEdit")  # For theming
        self.user_message_textedit.installEventFilter(self)  # To handle key events
        input_layout.addWidget(self.user_message_textedit)
        logger.debug("User message text edit added.")

        # Send Button
        send_button = QPushButton("Send")
        send_button.setIcon(QIcon(ICONS.get('send', '')))  # Ensure 'send' icon exists
        send_button.setObjectName("sendButton")  # For theming
        send_button.setFixedHeight(60)
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        logger.debug("Send button added and connected.")

        # Token Counter Label
        self.token_count_label = QLabel("Tokens: 0")
        self.token_count_label.setObjectName("tokenCountLabel")  # For theming
        self.token_count_label.setAlignment(Qt.AlignCenter)
        self.token_count_label.setFixedWidth(80)
        input_layout.addWidget(self.token_count_label)
        logger.debug("Token counter label added.")

        # Add input layout to main content
        layout.addLayout(input_layout)

        # Connect textChanged signal to update token counter
        self.user_message_textedit.textChanged.connect(self.update_token_counter)
        logger.debug("Main content area initialized.")

    def init_right_sidebar(self):
        """
        Initialize the right sidebar (if needed).
        """
        logger.debug("Initializing right sidebar.")
        self.right_sidebar = QWidget()
        layout = QVBoxLayout(self.right_sidebar)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Example: System Prompt Configuration
        system_prompt_label = QLabel("System Prompt:")
        system_prompt_label.setObjectName("systemPromptLabel")  # For theming
        layout.addWidget(system_prompt_label)

        self.system_prompt_analysis_textedit = QTextEdit()
        self.system_prompt_analysis_textedit.setPlainText(self.agent_system_prompt_content or "")
        self.system_prompt_analysis_textedit.textChanged.connect(self.sync_code_analysis_system_prompt_with_ui)
        self.system_prompt_analysis_textedit.setObjectName("systemPromptAnalysisTextEdit")  # For theming
        layout.addWidget(self.system_prompt_analysis_textedit)
        logger.debug("System prompt text edit added to right sidebar.")

        # Start Analysis Button
        start_analysis_button = QPushButton("Start Analysis")
        start_analysis_button.setIcon(QIcon(ICONS.get('start', '')))  # Ensure 'start' icon exists
        start_analysis_button.setObjectName("startAnalysisButton")  # For theming
        start_analysis_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(start_analysis_button)
        start_analysis_button.clicked.connect(self.start_code_analysis)
        logger.debug("Start Analysis button added and connected.")

        # Analysis Results
        self.analysis_results_textedit = QTextEdit()
        self.analysis_results_textedit.setReadOnly(True)
        self.analysis_results_textedit.setObjectName("analysisResultsTextEdit")  # For theming
        self.analysis_results_textedit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.analysis_results_textedit)
        logger.debug("Analysis results text edit added to right sidebar.")

        # Add stretch to push widgets to the top
        layout.addStretch()
        logger.debug("Right sidebar initialized.")

    def add_code_block(self, code_block, language='python'):
        """
        Add a code block to the Code Blocks tab.

        Args:
            code_block (str): The code block content.
            language (str): The programming language of the code block.
        """
        logger.debug("Adding code block to Code Blocks tab.")
        item_text = f"Language: {language}\n{code_block[:30]}..."  # Display first 30 chars
        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, {'code': code_block, 'language': language})
        self.code_blocks_list.addItem(item)
        logger.info("Code block added to Code Blocks tab.")

    def open_code_block(self, item):
        """
        Open the selected code block in a separate window.

        Args:
            item (QListWidgetItem): The selected list item.
        """
        logger.debug("Opening selected code block.")
        data = item.data(Qt.UserRole)
        if data:
            code = data.get('code', '')
            language = data.get('language', 'text')
            show_code_window(code, language)
            logger.info("Code block opened in CodeDisplayWindow.")

    def display_user_message(self, message):
        """
        Display the user's message in the chat display.
        Minimize code blocks by default.

        Args:
            message (str): The user's message.
        """
        logger.debug("Displaying user message: '%s'", message)
        # Detect code blocks
        code_block_pattern = r'```(\w+)?\n([\s\S]*?)\n```'
        matches = re.findall(code_block_pattern, message)
        logger.debug("Code blocks detected in user message: %s", matches)

        if matches:
            # Split message into text and code blocks
            parts = re.split(code_block_pattern, message)
            formatted_message = ""
            for i in range(len(parts)):
                if i % 3 == 0:
                    # Regular text
                    formatted_message += parts[i] + "\n\n"
                else:
                    # Code block
                    language = parts[i]
                    code = parts[i+1]
                    # Add code block with collapsible syntax
                    formatted_message += f"**User:** [Code Block ({language})](#)\n"
                    formatted_message += f"""<details>
    <summary>Click to expand/collapse</summary>
    ```{language}
{code}
```
</details>
"""
                    formatted_message += "\n\n"
                    # Store code block in Code Blocks tab
                    self.add_code_block(code, language)
                    break  # Assuming one code block per message
            self.append_markdown(formatted_message)
        else:
            formatted_message = f"**User:** {message}"
            self.append_markdown(formatted_message)

    def display_ai_message(self, message):
        """
        Display the AI's message in the chat display.

        Args:
            message (str): The AI's message.
        """
        logger.debug("Displaying AI message: '%s'", message)
        formatted_message = f"**AI:** {message}"
        self.append_markdown(formatted_message)

    def append_markdown(self, message):
        """
        Append a Markdown-formatted message to the chat display.

        Args:
            message (str): The Markdown-formatted message.
        """
        logger.debug("Appending Markdown message: '%s'", message)
        # Get current content
        current_content = self.chat_display.toPlainText()
        # Combine with new message
        new_content = f"{current_content}\n\n{message}"
        # Set the combined content with collapsible support
        self.chat_display.setMarkdown(new_content)
        logger.debug("Markdown message appended to chat display.")

    def update_token_counter(self):
        """
        Update the token counter label based on the content of the user message.
        """
        content = self.user_message_textedit.toPlainText()
        token_count = count_tokens_in_string(content)
        self.token_count_label.setText(f"Tokens: {token_count}")
        logger.debug(f"Token counter updated: {token_count} tokens.")

    def eventFilter(self, source, event):
        """
        Event filter to handle key events for auto-suggesting files and sending messages.

        Args:
            source: The source widget.
            event: The event object.
        """
        if event.type() == QEvent.KeyPress and source is self.user_message_textedit:
            if event.key() == Qt.Key_At:
                QTimer.singleShot(100, self.show_file_suggestions)
                logger.debug("At (@) key pressed in user message text edit. Showing file suggestions.")
                return True
            elif event.key() in (Qt.Key_Return, Qt.Key_Enter):  # Handle both Enter and Keypad Enter
                modifiers = event.modifiers()
                if modifiers & Qt.ShiftModifier:
                    # Insert a new line without sending the message
                    cursor = self.user_message_textedit.textCursor()
                    cursor.insertText('\n')
                    self.user_message_textedit.setTextCursor(cursor)
                    logger.debug("Shift+Enter pressed. New line inserted.")
                    return True
                else:
                    # Send the message if not Shift+Enter
                    logger.debug("Enter pressed. Sending message.")
                    self.send_message()
                    return True
        return super().eventFilter(source, event)

    def show_file_suggestions(self):
        """
        Show a context menu with file suggestions from the datamemory folder.
        """
        logger.debug("Showing file suggestions.")
        show_file_suggestions(self.user_message_textedit)

    def insert_file_name(self, file_name):
        """
        Insert the selected file name into the user message.

        Args:
            file_name (str): The file name to insert.
        """
        logger.debug("Inserting file name into user message: '%s'", file_name)
        insert_file_name(self.user_message_textedit, file_name)

    def update_model(self, model_name):
        """
        Update the AI model based on the selected model.

        Args:
            model_name (str): The name of the selected model.
        """
        logger.debug("Updating model to '%s'.", model_name)
        self.current_model_name = model_name
        try:
            llm = get_model(model_name)
            self.ai_service.update_model(model_name, llm=llm, temperature=self.temperature)
            logger.info("AI model updated to '%s'.", model_name)
        except ValueError as e:
            logger.error("Model update failed: %s", e)
            QMessageBox.critical(self, "Model Error", str(e))

    def update_temperature_from_slider(self, value):
        """
        Update the temperature value when the slider is moved.
        """
        temperature = value / 100
        logger.debug("Temperature slider moved to %d, updating temperature to %.2f.", value, temperature)
        self.temperature_spinbox.blockSignals(True)
        self.temperature_spinbox.setValue(temperature)
        self.temperature_spinbox.blockSignals(False)
        self.update_temperature(temperature)
        self.temperature_spinbox.setToolTip(f"Temperature: {temperature} (Controls randomness)")

    def update_temperature_from_spinbox(self, value):
        """
        Update the temperature value when the spinbox is changed.
        """
        temperature = value
        slider_value = int(value * 100)
        logger.debug("Temperature spinbox changed to %.2f, updating slider to %d.", temperature, slider_value)
        self.temperature_slider.blockSignals(True)
        self.temperature_slider.setValue(slider_value)
        self.temperature_slider.blockSignals(False)
        self.update_temperature(temperature)
        self.temperature_spinbox.setToolTip(f"Temperature: {temperature} (Controls randomness)")

    def update_temperature(self, temperature):
        """
        Update the temperature value.

        Args:
            temperature (float): The new temperature value.
        """
        logger.debug("Updating temperature to %.2f.", temperature)
        self.temperature = temperature
        self.config.CHAT_TEMPERATURE = temperature
        try:
            llm = get_model(self.current_model_name, temperature=temperature)
            self.ai_service.update_model(self.current_model_name, temperature=temperature)
            logger.info("Temperature updated to %.2f and AI model refreshed.", temperature)
        except ValueError as e:
            logger.error("Failed to update temperature: %s", e)
            QMessageBox.critical(self, "Model Error", str(e))

    def update_max_tokens_from_slider(self, value):
        """
        Update the max tokens value when the slider is moved.
        """
        logger.debug("Max tokens slider moved to %d.", value)
        self.max_tokens = value
        self.max_tokens_spinbox.blockSignals(True)
        self.max_tokens_spinbox.setValue(value)
        self.max_tokens_spinbox.blockSignals(False)
        self.update_max_tokens(value)
        self.max_tokens_spinbox.setToolTip(f"Max Tokens: {self.max_tokens}")

    def update_max_tokens_from_spinbox(self, value):
        """
        Update the max tokens value when the spinbox is changed.
        """
        logger.debug("Max tokens spinbox changed to %d.", value)
        self.max_tokens = value
        self.max_tokens_slider.blockSignals(True)
        self.max_tokens_slider.setValue(value)
        self.max_tokens_slider.blockSignals(False)
        self.update_max_tokens(value)
        self.max_tokens_spinbox.setToolTip(f"Max Tokens: {self.max_tokens}")

    def update_max_tokens(self, value):
        """
        Update the max tokens value.
        
        Args:
            value (int): The new max tokens value.
        """
        logger.debug("Updating max tokens to %d.", value)
        self.max_tokens = value
        self.config.MAX_TOKENS = value  # Ensure Config has MAX_TOKENS attribute
        try:
            self.ai_service.update_model(self.current_model_name, temperature=self.temperature)
            logger.info("Max tokens updated to %d and AI model refreshed.", value)
        except ValueError as e:
            logger.error("Failed to update max tokens: %s", e)
            QMessageBox.critical(self, "Model Error", str(e))

    def start_new_chat(self):
        """
        Start a new chat session.
        """
        logger.debug("Starting a new chat session.")
        self.current_chat_id = start_new_chat(self.chats, self.chat_history_list, self.chat_display)
        self.chat_history_content = []
        self.chat_display.setMarkdown("")
        logger.info("New chat session started with chat_id '%s'.", self.current_chat_id)

    def switch_chat(self, item):
        """
        Switch to a selected chat session.
        """
        chat_id = item.data(Qt.UserRole)
        logger.debug("Switching to chat_id '%s'.", chat_id)
        messages = switch_chat(chat_id, self.chats, self.chat_display)
        self.current_chat_id = chat_id
        self.chat_history_content = []
        self.chat_display.setMarkdown("")
        logger.debug("Displaying messages from chat_id '%s'.", chat_id)
        for message in messages:
            if message['role'] == 'user':
                self.display_user_message(message['content'])
                logger.debug("Displayed user message: '%s'", message['content'])
            else:
                self.display_ai_message(message['content'])
                logger.debug("Displayed AI message: '%s'", message['content'])

    def load_selected_chat(self):
        """
        Load the selected chat from chat history.
        """
        logger.debug("Loading selected chat.")
        item = self.chat_history_list.currentItem()
        if item:
            self.switch_chat(item)
            logger.info("Selected chat loaded successfully.")
        else:
            logger.warning("No chat selected to load.")
            QMessageBox.warning(self, "No Chat Selected", "Please select a chat to load.")

    def rename_selected_chat(self):
        """
        Rename the selected chat in the chat history.
        """
        logger.debug("Renaming selected chat.")
        rename_selected_chat(self.chat_history_list, self.chats)
        logger.info("Selected chat renamed.")

    def delete_selected_chat(self):
        """
        Delete the selected chat from the chat history.
        """
        logger.debug("Deleting selected chat.")
        success = delete_selected_chat(self.chat_history_list, self.chats)
        if success:
            self.chat_display.setMarkdown("")
            self.current_chat_id = None
            logger.info("Selected chat deleted successfully.")
        else:
            logger.warning("Failed to delete selected chat.")

    def clear_chat(self):
        """
        Clear the current chat history.
        """
        logger.debug("Clearing current chat.")
        if self.current_chat_id:
            self.chats[self.current_chat_id]['messages'] = []
            self.chat_display.setMarkdown("")
            save_chat_log(self.current_chat_id, self.chats[self.current_chat_id])
            logger.info("Chat history cleared for chat_id '%s'.", self.current_chat_id)
        else:
            logger.warning("No active chat to clear.")
            QMessageBox.warning(self, "No Chat Selected", "No chat session is currently active.")

    def load_chat_history(self):
        """
        Load chat history files into the chat history list.
        """
        logger.debug("Loading chat history.")
        load_chat_history(self.chat_history_list)
        logger.info("Chat history loaded.")

    def update_theme(self, theme_name):
        """
        Update the theme of this page.

        Args:
            theme_name (str): The name of the new theme.
        """
        logger.debug("Updating theme to '%s'.", theme_name)
        apply_theme(self, theme_name)
        # Update code block styles
        code_block_styles = ThemeManager.get_theme().get('CODE_BLOCK_STYLE', {})
        self.chat_display.apply_styles(code_block_styles)
        logger.info("Theme '%s' updated and code block styles applied.", theme_name)

    def on_load(self):
        """
        Called when the page is displayed.
        """
        logger.debug("Page loaded.")
        pass

    def on_unload(self):
        """
        Called when the page is hidden.
        """
        logger.debug("Page unloaded.")
        pass

    def upload_file(self):
        """
        Upload a file to the datamemory folder.
        """
        logger.debug("Uploading file.")
        upload_file(self)

    def view_files(self):
        """
        View files in the datamemory folder.
        """
        logger.debug("Viewing files.")
        view_files(self)

    def browse_input_directory(self):
        """
        Browse and select the input directory.
        """
        logger.debug("Browsing for input directory.")
        directory = QFileDialog.getExistingDirectory(self, "Select Input Directory")
        if directory:
            self.input_dir_lineedit.setText(directory)
            logger.info("Input directory selected: '%s'.", directory)

    def browse_output_directory(self):
        """
        Browse and select the output directory.
        """
        logger.debug("Browsing for output directory.")
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_lineedit.setText(directory)
            logger.info("Output directory selected: '%s'.", directory)

    # --- Code Analysis Methods ---
    def start_code_analysis(self):
        """
        Start the code analysis process in a separate thread.
        """
        logger.debug("Starting code analysis.")
        input_dir = self.input_dir_lineedit.text()
        output_dir = self.output_dir_lineedit.text()
        extensions = self.extensions_lineedit.text()
        system_prompt = self.system_prompt_analysis_textedit.toPlainText()

        logger.debug("Code analysis parameters - Input: '%s', Output: '%s', Extensions: '%s'",
                     input_dir, output_dir, extensions)

        if not input_dir or not output_dir:
            logger.warning("Input or Output directory not specified.")
            QMessageBox.warning(self, "Input Error", "Please specify both input and output directories.")
            return

        # Disable the start button and enable the stop button
        self.start_processing_button.setEnabled(False)
        self.stop_processing_button.setEnabled(True)  # Enable Stop button
        logger.debug("Start button disabled and Stop button enabled.")

        # Show the progress bar and processing log
        self.progress_bar.setVisible(True)
        self.processing_log.setVisible(True)
        self.progress_bar.setValue(0)
        self.processing_log.clear()
        logger.debug("Progress bar and processing log made visible and reset.")

        # Get the selected model
        try:
            llm = get_model(self.current_model_name)
            logger.debug("LLM model '%s' retrieved successfully for code analysis.", self.current_model_name)
        except ValueError as e:
            logger.error("Model retrieval failed: %s", e)
            QMessageBox.critical(self, "Model Error", str(e))
            self.start_processing_button.setEnabled(True)
            self.stop_processing_button.setEnabled(False)  # Disable Stop button
            return

        # Create a QThread
        self.thread = QThread()
        self.worker = Worker(input_dir, output_dir, system_prompt, llm)
        self.worker.moveToThread(self.thread)
        logger.debug("Worker moved to new thread.")

        # Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.processing_finished.connect(self.on_processing_finished)
        self.worker.processing_finished.connect(self.thread.quit)
        self.worker.processing_finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Start the thread
        self.thread.start()
        logger.info("Code analysis thread started.")

    def stop_processing_files(self):
        """
        Stop the ongoing processing of Markdown files.
        """
        logger.debug("Stopping file processing.")
        if hasattr(self, 'worker') and self.worker is not None:
            self.worker.stop()
            self.processing_log.append("Stopping processing...")
            self.stop_processing_button.setEnabled(False)  # Disable Stop button to prevent multiple clicks
            logger.info("Stop processing requested.")
        else:
            logger.warning("No processing task is currently running.")
            QMessageBox.warning(self, "No Processing Task", "There is no processing task to stop.")

    def update_progress(self, item_name, status):
        """
        Update the progress bar and processing log based on progress updates.

        Args:
            item_name (str): The name of the item being processed.
            status (str): The current status of the item.
        """
        logger.debug("Updating progress - Item: '%s', Status: '%s'", item_name, status)
        # Update the progress bar
        if item_name == "All Files" and status == "Completed":
            self.progress_bar.setValue(100)
            logger.debug("All files processed. Progress bar set to 100%.")
        elif item_name == "All Files":
            pass  # Do not update progress bar for individual files
        else:
            # For simplicity, increment by 1 for each processed item
            current_value = self.progress_bar.value()
            if current_value < 100:
                self.progress_bar.setValue(current_value + 1)
                logger.debug("Progress bar incremented to %d%%.", current_value + 1)

        # Append to the processing log
        self.processing_log.append(f"{item_name}: {status}")
        logger.debug("Processing log updated with item '%s' status '%s'.", item_name, status)

    def on_processing_finished(self):
        """
        Handle the completion of file processing.
        """
        logger.info("File processing completed.")
        QMessageBox.information(self, "Processing Complete", "Markdown files have been processed.")
        self.progress_bar.setVisible(False)
        self.processing_log.setVisible(False)
        self.start_processing_button.setEnabled(True)
        self.stop_processing_button.setEnabled(False)  # Disable Stop button after completion
        logger.debug("Processing UI elements reset.")

    def sync_code_analysis_system_prompt_with_ui(self):
        """
        Sync the changes made in the Code Analysis system prompt text box with the actual markdown file.
        """
        if self.system_prompt_analysis_textedit is not None:
            updated_prompt_content = self.system_prompt_analysis_textedit.toPlainText()
            save_system_prompt(updated_prompt_content)
            logger.debug("System prompt for code analysis synced with UI.")
        else:
            logger.error("system_prompt_analysis_textedit is None, cannot sync with UI.")

    def update_system_prompt(self, prompt_name):
        """
        Update the system prompt based on the selected prompt.

        Args:
            prompt_name (str): The name of the selected prompt.
        """
        logger.debug("Updating system prompt to '%s'.", prompt_name)
        prompt_content = load_specific_system_prompt(prompt_name)
        if prompt_content:
            self.agent_system_prompt_content = prompt_content
            logger.debug("System prompt content loaded.")

            # Update the system prompt in Code Analysis Tool
            if hasattr(self, 'system_prompt_analysis_textedit') and self.system_prompt_analysis_textedit is not None:
                self.system_prompt_analysis_textedit.setPlainText(prompt_content)
                logger.debug("System prompt text edit updated with new content.")
            else:
                logger.error("system_prompt_analysis_textedit is None, cannot setPlainText.")
        else:
            logger.warning("No content found for system prompt '%s'.", prompt_name)

    def toggle_agent_mode(self, agent_type: str, checked: bool):
        """
        Toggle the agent (developer or crew) mode based on the QCheckBox state.

        Args:
            agent_type (str): The type of agent ('developer' or 'crew').
            checked (bool): The state of the checkbox.
        """
        logger.info("Toggling %s mode to %s.", agent_type, "Enabled" if checked else "Disabled")
        enabled = checked
        logger.debug("toggle_agent_mode: agent_type=%s, enabled=%s", agent_type, enabled)

        try:
            # Get current config for the specific agent
            current_config = self.config.get_agent_config(agent_type)
            current_workflow = current_config.get('profile', {}).get('config', {}).get('current_workflow')

            settings = {}
            if enabled:
                # Determine which workflow to set based on agent type
                if agent_type == 'developer':
                    selected_workflow = self.developer_workflow_combobox.currentText().split(" - ")[0].lower()
                elif agent_type == 'crew':
                    selected_workflow = self.crew_workflow_combobox.currentText().split(" - ")[0].lower()
                else:
                    selected_workflow = 'none'

                settings['current_workflow'] = current_workflow or selected_workflow
                logger.debug("Selected workflow for %s: %s", agent_type, settings['current_workflow'])

            # Pass enabled state explicitly
            success = self.ai_service.update_agent(
                agent_type=agent_type,
                enabled=enabled,  # This ensures AGENT_ENABLED matches checkbox
                settings=settings
            )

            if success:
                if agent_type == 'developer':
                    self.developer_workflow_combobox.setEnabled(enabled)
                elif agent_type == 'crew':
                    self.crew_workflow_combobox.setEnabled(enabled)
                self.agent_status_label.setText(
                    f"Developer Agent: {'Enabled' if self.developer_toggle.isChecked() else 'Disabled'} | "
                    f"Crew Agent: {'Enabled' if self.crew_toggle.isChecked() else 'Disabled'}"
                )
                workflow_text = f"Developer Workflow: {settings.get('current_workflow', 'None') if agent_type == 'developer' else 'None'} | " \
                                f"Crew Workflow: {settings.get('current_workflow', 'None') if agent_type == 'crew' else 'None'}"
                self.workflow_status.setText(workflow_text)
                self.workflow_status.setStyleSheet("color: green;" if enabled else "color: gray;")
                self.update_status_message(f"{agent_type.capitalize()} Agent {'Enabled' if enabled else 'Disabled'}", is_agent_message=True)
                logger.info("%s mode toggled successfully to %s.", agent_type.capitalize(), "Enabled" if enabled else "Disabled")
            else:
                # Revert the checkbox state if update failed
                if agent_type == 'developer':
                    self.developer_toggle.setChecked(not enabled)
                elif agent_type == 'crew':
                    self.crew_toggle.setChecked(not enabled)
                QMessageBox.warning(self, "Agent Mode Error", f"Failed to update {agent_type} mode")
                logger.warning("Failed to toggle %s mode.", agent_type)
                
        except Exception as e:
            logger.error("Error in toggle_agent_mode for %s: %s", agent_type, e)
            # Revert the checkbox state in case of error
            if agent_type == 'developer':
                self.developer_toggle.setChecked(not enabled)
            elif agent_type == 'crew':
                self.crew_toggle.setChecked(not enabled)
            QMessageBox.critical(self, "Error", f"Failed to toggle {agent_type} mode: {str(e)}")
            logger.debug("Checkbox state reverted due to error.")

    def update_status_message(self, message, is_agent_message=False):
        """
        Update the status message in the status bar.

        Args:
            message (str): The message to display.
            is_agent_message (bool): Whether the message is related to the agent.
        """
        logger.debug("Updating status message to '%s' (is_agent_message=%s).", message, is_agent_message)
        self.status_label.setText(message)
        if is_agent_message:
            self.status_label.setStyleSheet("color: green;")  # You can customize the color as needed
        else:
            self.status_label.setStyleSheet("color: black;")  # Default color
        logger.info("Status message updated: %s", message)

    def send_message(self):
        """
        Handle sending a message.
        """
        logger.debug("send_message called.")
        message = self.user_message_textedit.toPlainText().strip()
        logger.debug("User message retrieved: '%s'", message)
        if message:
            # Display the user's message
            self.display_user_message(message)
            logger.debug("User message displayed.")

            # Add the message to the chat history
            add_to_chat_history(self.current_chat_id, self.chats, {'role': 'user', 'content': message})
            logger.debug("User message added to chat history.")

            # Prepare the messages for the AI model
            system_prompt = self.agent_system_prompt_content
            user_message = message
            memory = load_memory()
            messages = prepare_messages(system_prompt, user_message, self.current_model_name, self.config)
            logger.debug("Messages prepared for AI model: %s", messages)

            # Update status to show processing
            self.update_status_message("Processing message...", is_agent_message=True)
            logger.debug("Status message updated to 'Processing message...'.")

            # Start a worker thread to get AI response
            self.worker_thread = WorkerThread(messages, self.ai_service)
            self.worker_thread.response_ready.connect(self.handle_ai_response)
            self.worker_thread.error_occurred.connect(self.handle_ai_error)
            self.worker_thread.code_blocks_found.connect(self.handle_code_blocks)
            self.worker_thread.start()
            logger.debug("Worker thread started for AI response.")

            # Clear the user message text edit
            self.user_message_textedit.clear()
            logger.debug("User message text edit cleared.")
        else:
            logger.debug("No message to send.")

    def handle_ai_response(self, response_content, additional_data):
        """
        Handle the AI's response when it's ready.
        """
        logger.debug("handle_ai_response called with response_content: '%s'", response_content)
        # Detect code blocks using regex
        code_block_pattern = r'```(\w+)?\n([\s\S]*?)\n```'
        matches = re.findall(code_block_pattern, response_content)
        logger.debug("Code blocks detected: %s", matches)

        # Remove code blocks from the main response
        clean_response = re.sub(code_block_pattern, '', response_content).strip()
        logger.debug("Clean AI response after removing code blocks: '%s'", clean_response)

        # Display the clean AI message
        if clean_response:
            self.display_ai_message(clean_response)
            logger.debug("AI message displayed.")

            # Add the AI's message to the chat history
            add_to_chat_history(self.current_chat_id, self.chats, {'role': 'assistant', 'content': clean_response})
            logger.debug("AI message added to chat history.")

        # Handle each detected code block
        for match in matches:
            language = match[0] if match[0] else 'text'
            code = match[1]
            logger.info("Code block found (%s): %s", language, code)

            # Display the code block in a separate window
            show_code_window(code, language)
            logger.debug("Code block displayed in separate window.")

            # Optionally, add the code block to chat history if desired
            # Uncomment the following lines if you want code blocks to appear in the chat history
            # formatted_code = f"**Code ({language}):**\n```{language}\n{code}\n```"
            # self.display_ai_message(formatted_code)
            # add_to_chat_history(self.current_chat_id, self.chats, {'role': 'assistant', 'content': formatted_code})

        # Save the chat log
        save_chat_log(self.current_chat_id, self.chats[self.current_chat_id])
        logger.debug("Chat log saved for chat_id '%s'.", self.current_chat_id)

        # Update status to show completion
        agent_config = self.config.get_agent_config('developer')
        status_message = "Response received"
        if agent_config['enabled']:
            agent_name = agent_config['profile'].get('name', 'Agent')
            status_message += f" from {agent_name}"
        self.update_status_message(status_message, is_agent_message=True)
        logger.debug("Status message updated to '%s'.", status_message)

    def handle_ai_error(self, error_message):
        """
        Handle any errors that occur during AI processing.

        Args:
            error_message (str): The error message.
        """
        logger.error("AI Error occurred: %s", error_message)
        QMessageBox.critical(self, "AI Error", f"An error occurred: {error_message}")

    def handle_code_blocks(self, code_blocks):
        """
        Handle code blocks found in the AI's response.

        Args:
            code_blocks (list): List of code blocks.
        """
        logger.debug("Handling code blocks: %s", code_blocks)
        for code_block in code_blocks:
            language = code_block['language']
            code = code_block['code']
            logger.info("Code block found (%s): %s", language, code)

            # Display the code block in a separate window
            show_code_window(code, language)
            logger.debug("Code block displayed in separate window.")

    def display_user_message(self, message):
        """
        Display the user's message in the chat display.
        Minimize code blocks by default.

        Args:
            message (str): The user's message.
        """
        logger.debug("Displaying user message: '%s'", message)
        # Detect code blocks
        code_block_pattern = r'```(\w+)?\n([\s\S]*?)\n```'
        matches = re.findall(code_block_pattern, message)
        logger.debug("Code blocks detected in user message: %s", matches)

        if matches:
            # Split message into text and code blocks
            parts = re.split(code_block_pattern, message)
            formatted_message = ""
            for i in range(len(parts)):
                if i % 3 == 0:
                    # Regular text
                    formatted_message += parts[i] + "\n\n"
                else:
                    # Code block
                    language = parts[i]
                    code = parts[i+1]
                    # Add code block with collapsible syntax
                    formatted_message += f"**User:** [Code Block ({language})](#)\n"
                    formatted_message += f"""<details>
<summary>Click to expand/collapse</summary>
```{language}
{code}
```
</details>
"""
                    formatted_message += "\n\n"
                    # Store code block in Code Blocks tab
                    self.add_code_block(code, language)
                    break  # Assuming one code block per message
            self.append_markdown(formatted_message)
        else:
            formatted_message = f"**User:** {message}"
            self.append_markdown(formatted_message)

    def display_ai_message(self, message):
        """
        Display the AI's message in the chat display.

        Args:
            message (str): The AI's message.
        """
        logger.debug("Displaying AI message: '%s'", message)
        formatted_message = f"**AI:** {message}"
        self.append_markdown(formatted_message)

    def append_markdown(self, message):
        """
        Append a Markdown-formatted message to the chat display.

        Args:
            message (str): The Markdown-formatted message.
        """
        logger.debug("Appending Markdown message: '%s'", message)
        # Get current content
        current_content = self.chat_display.toPlainText()
        # Combine with new message
        new_content = f"{current_content}\n\n{message}"
        # Set the combined content with collapsible support
        self.chat_display.setMarkdown(new_content)
        logger.debug("Markdown message appended to chat display.")

    def update_token_counter(self):
        """
        Update the token counter label based on the content of the user message.
        """
        content = self.user_message_textedit.toPlainText()
        token_count = count_tokens_in_string(content)
        self.token_count_label.setText(f"Tokens: {token_count}")
        logger.debug(f"Token counter updated: {token_count} tokens.")

    def eventFilter(self, source, event):
        """
        Event filter to handle key events for auto-suggesting files and sending messages.

        Args:
            source: The source widget.
            event: The event object.
        """
        if event.type() == QEvent.KeyPress and source is self.user_message_textedit:
            if event.key() == Qt.Key_At:
                QTimer.singleShot(100, self.show_file_suggestions)
                logger.debug("At (@) key pressed in user message text edit. Showing file suggestions.")
                return True
            elif event.key() in (Qt.Key_Return, Qt.Key_Enter):  # Handle both Enter and Keypad Enter
                modifiers = event.modifiers()
                if modifiers & Qt.ShiftModifier:
                    # Insert a new line without sending the message
                    cursor = self.user_message_textedit.textCursor()
                    cursor.insertText('\n')
                    self.user_message_textedit.setTextCursor(cursor)
                    logger.debug("Shift+Enter pressed. New line inserted.")
                    return True
                else:
                    # Send the message if not Shift+Enter
                    logger.debug("Enter pressed. Sending message.")
                    self.send_message()
                    return True
        return super().eventFilter(source, event)

    def show_file_suggestions(self):
        """
        Show a context menu with file suggestions from the datamemory folder.
        """
        logger.debug("Showing file suggestions.")
        show_file_suggestions(self.user_message_textedit)

    def insert_file_name(self, file_name):
        """
        Insert the selected file name into the user message.

        Args:
            file_name (str): The file name to insert.
        """
        logger.debug("Inserting file name into user message: '%s'", file_name)
        insert_file_name(self.user_message_textedit, file_name)

    def update_model(self, model_name):
        """
        Update the AI model based on the selected model.

        Args:
            model_name (str): The name of the selected model.
        """
        logger.debug("Updating model to '%s'.", model_name)
        self.current_model_name = model_name
        try:
            llm = get_model(model_name)
            self.ai_service.update_model(model_name, llm=llm, temperature=self.temperature)
            logger.info("AI model updated to '%s'.", model_name)
        except ValueError as e:
            logger.error("Model update failed: %s", e)
            QMessageBox.critical(self, "Model Error", str(e))

    def update_temperature_from_slider(self, value):
        """
        Update the temperature value when the slider is moved.
        """
        temperature = value / 100
        logger.debug("Temperature slider moved to %d, updating temperature to %.2f.", value, temperature)
        self.temperature_spinbox.blockSignals(True)
        self.temperature_spinbox.setValue(temperature)
        self.temperature_spinbox.blockSignals(False)
        self.update_temperature(temperature)
        self.temperature_spinbox.setToolTip(f"Temperature: {temperature} (Controls randomness)")

    def update_temperature_from_spinbox(self, value):
        """
        Update the temperature value when the spinbox is changed.
        """
        temperature = value
        slider_value = int(value * 100)
        logger.debug("Temperature spinbox changed to %.2f, updating slider to %d.", temperature, slider_value)
        self.temperature_slider.blockSignals(True)
        self.temperature_slider.setValue(slider_value)
        self.temperature_slider.blockSignals(False)
        self.update_temperature(temperature)
        self.temperature_spinbox.setToolTip(f"Temperature: {temperature} (Controls randomness)")

    def update_temperature(self, temperature):
        """
        Update the temperature value.

        Args:
            temperature (float): The new temperature value.
        """
        logger.debug("Updating temperature to %.2f.", temperature)
        self.temperature = temperature
        self.config.CHAT_TEMPERATURE = temperature
        try:
            llm = get_model(self.current_model_name, temperature=temperature)
            self.ai_service.update_model(self.current_model_name, temperature=temperature)
            logger.info("Temperature updated to %.2f and AI model refreshed.", temperature)
        except ValueError as e:
            logger.error("Failed to update temperature: %s", e)
            QMessageBox.critical(self, "Model Error", str(e))

    def update_max_tokens_from_slider(self, value):
        """
        Update the max tokens value when the slider is moved.
        """
        logger.debug("Max tokens slider moved to %d.", value)
        self.max_tokens = value
        self.max_tokens_spinbox.blockSignals(True)
        self.max_tokens_spinbox.setValue(value)
        self.max_tokens_spinbox.blockSignals(False)
        self.update_max_tokens(value)
        self.max_tokens_spinbox.setToolTip(f"Max Tokens: {self.max_tokens}")

    def update_max_tokens_from_spinbox(self, value):
        """
        Update the max tokens value when the spinbox is changed.
        """
        logger.debug("Max tokens spinbox changed to %d.", value)
        self.max_tokens = value
        self.max_tokens_slider.blockSignals(True)
        self.max_tokens_slider.setValue(value)
        self.max_tokens_slider.blockSignals(False)
        self.update_max_tokens(value)
        self.max_tokens_spinbox.setToolTip(f"Max Tokens: {self.max_tokens}")

    def update_max_tokens(self, value):
        """
        Update the max tokens value.
        
        Args:
            value (int): The new max tokens value.
        """
        logger.debug("Updating max tokens to %d.", value)
        self.max_tokens = value
        self.config.MAX_TOKENS = value  # Ensure Config has MAX_TOKENS attribute
        try:
            self.ai_service.update_model(self.current_model_name, temperature=self.temperature)
            logger.info("Max tokens updated to %d and AI model refreshed.", value)
        except ValueError as e:
            logger.error("Failed to update max tokens: %s", e)
            QMessageBox.critical(self, "Model Error", str(e))

    def start_new_chat(self):
        """
        Start a new chat session.
        """
        logger.debug("Starting a new chat session.")
        self.current_chat_id = start_new_chat(self.chats, self.chat_history_list, self.chat_display)
        self.chat_history_content = []
        self.chat_display.setMarkdown("")
        logger.info("New chat session started with chat_id '%s'.", self.current_chat_id)

    def switch_chat(self, item):
        """
        Switch to a selected chat session.
        """
        chat_id = item.data(Qt.UserRole)
        logger.debug("Switching to chat_id '%s'.", chat_id)
        messages = switch_chat(chat_id, self.chats, self.chat_display)
        self.current_chat_id = chat_id
        self.chat_history_content = []
        self.chat_display.setMarkdown("")
        logger.debug("Displaying messages from chat_id '%s'.", chat_id)
        for message in messages:
            if message['role'] == 'user':
                self.display_user_message(message['content'])
                logger.debug("Displayed user message: '%s'", message['content'])
            else:
                self.display_ai_message(message['content'])
                logger.debug("Displayed AI message: '%s'", message['content'])

    def load_selected_chat(self):
        """
        Load the selected chat from chat history.
        """
        logger.debug("Loading selected chat.")
        item = self.chat_history_list.currentItem()
        if item:
            self.switch_chat(item)
            logger.info("Selected chat loaded successfully.")
        else:
            logger.warning("No chat selected to load.")
            QMessageBox.warning(self, "No Chat Selected", "Please select a chat to load.")

    def rename_selected_chat(self):
        """
        Rename the selected chat in the chat history.
        """
        logger.debug("Renaming selected chat.")
        rename_selected_chat(self.chat_history_list, self.chats)
        logger.info("Selected chat renamed.")

    def delete_selected_chat(self):
        """
        Delete the selected chat from the chat history.
        """
        logger.debug("Deleting selected chat.")
        success = delete_selected_chat(self.chat_history_list, self.chats)
        if success:
            self.chat_display.setMarkdown("")
            self.current_chat_id = None
            logger.info("Selected chat deleted successfully.")
        else:
            logger.warning("Failed to delete selected chat.")

    def clear_chat(self):
        """
        Clear the current chat history.
        """
        logger.debug("Clearing current chat.")
        if self.current_chat_id:
            self.chats[self.current_chat_id]['messages'] = []
            self.chat_display.setMarkdown("")
            save_chat_log(self.current_chat_id, self.chats[self.current_chat_id])
            logger.info("Chat history cleared for chat_id '%s'.", self.current_chat_id)
        else:
            logger.warning("No active chat to clear.")
            QMessageBox.warning(self, "No Chat Selected", "No chat session is currently active.")

    def load_chat_history(self):
        """
        Load chat history files into the chat history list.
        """
        logger.debug("Loading chat history.")
        load_chat_history(self.chat_history_list)
        logger.info("Chat history loaded.")

    def update_theme(self, theme_name):
        """
        Update the theme of this page.

        Args:
            theme_name (str): The name of the new theme.
        """
        logger.debug("Updating theme to '%s'.", theme_name)
        apply_theme(self, theme_name)
        # Update code block styles
        code_block_styles = ThemeManager.get_theme().get('CODE_BLOCK_STYLE', {})
        self.chat_display.apply_styles(code_block_styles)
        logger.info("Theme '%s' updated and code block styles applied.", theme_name)

    def on_load(self):
        """
        Called when the page is displayed.
        """
        logger.debug("Page loaded.")
        pass

    def on_unload(self):
        """
        Called when the page is hidden.
        """
        logger.debug("Page unloaded.")
        pass

    def upload_file(self):
        """
        Upload a file to the datamemory folder.
        """
        logger.debug("Uploading file.")
        upload_file(self)

    def view_files(self):
        """
        View files in the datamemory folder.
        """
        logger.debug("Viewing files.")
        view_files(self)

    def browse_input_directory(self):
        """
        Browse and select the input directory.
        """
        logger.debug("Browsing for input directory.")
        directory = QFileDialog.getExistingDirectory(self, "Select Input Directory")
        if directory:
            self.input_dir_lineedit.setText(directory)
            logger.info("Input directory selected: '%s'.", directory)

    def browse_output_directory(self):
        """
        Browse and select the output directory.
        """
        logger.debug("Browsing for output directory.")
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_lineedit.setText(directory)
            logger.info("Output directory selected: '%s'.", directory)

    # --- Code Analysis Methods ---
    def start_code_analysis(self):
        """
        Start the code analysis process in a separate thread.
        """
        logger.debug("Starting code analysis.")
        input_dir = self.input_dir_lineedit.text()
        output_dir = self.output_dir_lineedit.text()
        extensions = self.extensions_lineedit.text()
        system_prompt = self.system_prompt_analysis_textedit.toPlainText()

        logger.debug("Code analysis parameters - Input: '%s', Output: '%s', Extensions: '%s'",
                     input_dir, output_dir, extensions)

        if not input_dir or not output_dir:
            logger.warning("Input or Output directory not specified.")
            QMessageBox.warning(self, "Input Error", "Please specify both input and output directories.")
            return

        # Disable the start button and enable the stop button
        self.start_processing_button.setEnabled(False)
        self.stop_processing_button.setEnabled(True)  # Enable Stop button
        logger.debug("Start button disabled and Stop button enabled.")

        # Show the progress bar and processing log
        self.progress_bar.setVisible(True)
        self.processing_log.setVisible(True)
        self.progress_bar.setValue(0)
        self.processing_log.clear()
        logger.debug("Progress bar and processing log made visible and reset.")

        # Get the selected model
        try:
            llm = get_model(self.current_model_name)
            logger.debug("LLM model '%s' retrieved successfully for code analysis.", self.current_model_name)
        except ValueError as e:
            logger.error("Model retrieval failed: %s", e)
            QMessageBox.critical(self, "Model Error", str(e))
            self.start_processing_button.setEnabled(True)
            self.stop_processing_button.setEnabled(False)  # Disable Stop button
            return

        # Create a QThread
        self.thread = QThread()
        self.worker = Worker(input_dir, output_dir, system_prompt, llm)
        self.worker.moveToThread(self.thread)
        logger.debug("Worker moved to new thread.")

        # Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.processing_finished.connect(self.on_processing_finished)
        self.worker.processing_finished.connect(self.thread.quit)
        self.worker.processing_finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Start the thread
        self.thread.start()
        logger.info("Code analysis thread started.")

    def stop_processing_files(self):
        """
        Stop the ongoing processing of Markdown files.
        """
        logger.debug("Stopping file processing.")
        if hasattr(self, 'worker') and self.worker is not None:
            self.worker.stop()
            self.processing_log.append("Stopping processing...")
            self.stop_processing_button.setEnabled(False)  # Disable Stop button to prevent multiple clicks
            logger.info("Stop processing requested.")
        else:
            logger.warning("No processing task is currently running.")
            QMessageBox.warning(self, "No Processing Task", "There is no processing task to stop.")

    def update_progress(self, item_name, status):
        """
        Update the progress bar and processing log based on progress updates.

        Args:
            item_name (str): The name of the item being processed.
            status (str): The current status of the item.
        """
        logger.debug("Updating progress - Item: '%s', Status: '%s'", item_name, status)
        # Update the progress bar
        if item_name == "All Files" and status == "Completed":
            self.progress_bar.setValue(100)
            logger.debug("All files processed. Progress bar set to 100%.")
        elif item_name == "All Files":
            pass  # Do not update progress bar for individual files
        else:
            # For simplicity, increment by 1 for each processed item
            current_value = self.progress_bar.value()
            if current_value < 100:
                self.progress_bar.setValue(current_value + 1)
                logger.debug("Progress bar incremented to %d%%.", current_value + 1)

        # Append to the processing log
        self.processing_log.append(f"{item_name}: {status}")
        logger.debug("Processing log updated with item '%s' status '%s'.", item_name, status)

    def on_processing_finished(self):
        """
        Handle the completion of file processing.
        """
        logger.info("File processing completed.")
        QMessageBox.information(self, "Processing Complete", "Markdown files have been processed.")
        self.progress_bar.setVisible(False)
        self.processing_log.setVisible(False)
        self.start_processing_button.setEnabled(True)
        self.stop_processing_button.setEnabled(False)  # Disable Stop button after completion
        logger.debug("Processing UI elements reset.")

    def sync_code_analysis_system_prompt_with_ui(self):
        """
        Sync the changes made in the Code Analysis system prompt text box with the actual markdown file.
        """
        if self.system_prompt_analysis_textedit is not None:
            updated_prompt_content = self.system_prompt_analysis_textedit.toPlainText()
            save_system_prompt(updated_prompt_content)
            logger.debug("System prompt for code analysis synced with UI.")
        else:
            logger.error("system_prompt_analysis_textedit is None, cannot sync with UI.")

    def update_system_prompt(self, prompt_name):
        """
        Update the system prompt based on the selected prompt.

        Args:
            prompt_name (str): The name of the selected prompt.
        """
        logger.debug("Updating system prompt to '%s'.", prompt_name)
        prompt_content = load_specific_system_prompt(prompt_name)
        if prompt_content:
            self.agent_system_prompt_content = prompt_content
            logger.debug("System prompt content loaded.")

            # Update the system prompt in Code Analysis Tool
            if hasattr(self, 'system_prompt_analysis_textedit') and self.system_prompt_analysis_textedit is not None:
                self.system_prompt_analysis_textedit.setPlainText(prompt_content)
                logger.debug("System prompt text edit updated with new content.")
            else:
                logger.error("system_prompt_analysis_textedit is None, cannot setPlainText.")
        else:
            logger.warning("No content found for system prompt '%s'.", prompt_name)

    def toggle_agent_mode(self, agent_type: str, checked: bool):
        """
        Toggle the agent (developer or crew) mode based on the QCheckBox state.

        Args:
            agent_type (str): The type of agent ('developer' or 'crew').
            checked (bool): The state of the checkbox.
        """
        logger.info("Toggling %s mode to %s.", agent_type, "Enabled" if checked else "Disabled")
        enabled = checked
        logger.debug("toggle_agent_mode: agent_type=%s, enabled=%s", agent_type, enabled)

        try:
            # Get current config for the specific agent
            current_config = self.config.get_agent_config(agent_type)
            current_workflow = current_config.get('profile', {}).get('config', {}).get('current_workflow')

            settings = {}
            if enabled:
                # Determine which workflow to set based on agent type
                if agent_type == 'developer':
                    selected_workflow = self.developer_workflow_combobox.currentText().split(" - ")[0].lower()
                elif agent_type == 'crew':
                    selected_workflow = self.crew_workflow_combobox.currentText().split(" - ")[0].lower()
                else:
                    selected_workflow = 'none'

                settings['current_workflow'] = current_workflow or selected_workflow
                logger.debug("Selected workflow for %s: %s", agent_type, settings['current_workflow'])

            # Pass enabled state explicitly
            success = self.ai_service.update_agent(
                agent_type=agent_type,
                enabled=enabled,  # This ensures AGENT_ENABLED matches checkbox
                settings=settings
            )

            if success:
                if agent_type == 'developer':
                    self.developer_workflow_combobox.setEnabled(enabled)
                elif agent_type == 'crew':
                    self.crew_workflow_combobox.setEnabled(enabled)
                self.agent_status_label.setText(
                    f"Developer Agent: {'Enabled' if self.developer_toggle.isChecked() else 'Disabled'} | "
                    f"Crew Agent: {'Enabled' if self.crew_toggle.isChecked() else 'Disabled'}"
                )
                workflow_text = f"Developer Workflow: {settings.get('current_workflow', 'None') if agent_type == 'developer' else 'None'} | " \
                                f"Crew Workflow: {settings.get('current_workflow', 'None') if agent_type == 'crew' else 'None'}"
                self.workflow_status.setText(workflow_text)
                self.workflow_status.setStyleSheet("color: green;" if enabled else "color: gray;")
                self.update_status_message(f"{agent_type.capitalize()} Agent {'Enabled' if enabled else 'Disabled'}", is_agent_message=True)
                logger.info("%s mode toggled successfully to %s.", agent_type.capitalize(), "Enabled" if enabled else "Disabled")
            else:
                # Revert the checkbox state if update failed
                if agent_type == 'developer':
                    self.developer_toggle.setChecked(not enabled)
                elif agent_type == 'crew':
                    self.crew_toggle.setChecked(not enabled)
                QMessageBox.warning(self, "Agent Mode Error", f"Failed to update {agent_type} mode")
                logger.warning("Failed to toggle %s mode.", agent_type)

        except Exception as e:
            logger.error("Error in toggle_agent_mode for %s: %s", agent_type, e)
            # Revert the checkbox state in case of error
            if agent_type == 'developer':
                self.developer_toggle.setChecked(not enabled)
            elif agent_type == 'crew':
                self.crew_toggle.setChecked(not enabled)
            QMessageBox.critical(self, "Error", f"Failed to toggle {agent_type} mode: {str(e)}")
            logger.debug("Checkbox state reverted due to error.")

    def update_status_message(self, message, is_agent_message=False):
        """
        Update the status message in the status bar.

        Args:
            message (str): The message to display.
            is_agent_message (bool): Whether the message is related to the agent.
        """
        logger.debug("Updating status message to '%s' (is_agent_message=%s).", message, is_agent_message)
        self.status_label.setText(message)
        if is_agent_message:
            self.status_label.setStyleSheet("color: green;")  # You can customize the color as needed
        else:
            self.status_label.setStyleSheet("color: black;")  # Default color
        logger.info("Status message updated: %s", message)

    def send_message(self):
        """
        Handle sending a message.
        """
        logger.debug("send_message called.")
        message = self.user_message_textedit.toPlainText().strip()
        logger.debug("User message retrieved: '%s'", message)
        if message:
            # Display the user's message
            self.display_user_message(message)
            logger.debug("User message displayed.")

            # Add the message to the chat history
            add_to_chat_history(self.current_chat_id, self.chats, {'role': 'user', 'content': message})
            logger.debug("User message added to chat history.")

            # Prepare the messages for the AI model
            system_prompt = self.agent_system_prompt_content
            user_message = message
            memory = load_memory()
            messages = prepare_messages(system_prompt, user_message, self.current_model_name, self.config)
            logger.debug("Messages prepared for AI model: %s", messages)

            # Update status to show processing
            self.update_status_message("Processing message...", is_agent_message=True)
            logger.debug("Status message updated to 'Processing message...'.")

            # Start a worker thread to get AI response
            self.worker_thread = WorkerThread(messages, self.ai_service)
            self.worker_thread.response_ready.connect(self.handle_ai_response)
            self.worker_thread.error_occurred.connect(self.handle_ai_error)
            self.worker_thread.code_blocks_found.connect(self.handle_code_blocks)
            self.worker_thread.start()
            logger.debug("Worker thread started for AI response.")

            # Clear the user message text edit
            self.user_message_textedit.clear()
            logger.debug("User message text edit cleared.")
        else:
            logger.debug("No message to send.")

    def handle_ai_response(self, response_content, additional_data):
        """
        Handle the AI's response when it's ready.
        """
        logger.debug("handle_ai_response called with response_content: '%s'", response_content)
        # Detect code blocks using regex
        code_block_pattern = r'```(\w+)?\n([\s\S]*?)\n```'
        matches = re.findall(code_block_pattern, response_content)
        logger.debug("Code blocks detected: %s", matches)

        # Remove code blocks from the main response
        clean_response = re.sub(code_block_pattern, '', response_content).strip()
        logger.debug("Clean AI response after removing code blocks: '%s'", clean_response)

        # Display the clean AI message
        if clean_response:
            self.display_ai_message(clean_response)
            logger.debug("AI message displayed.")

            # Add the AI's message to the chat history
            add_to_chat_history(self.current_chat_id, self.chats, {'role': 'assistant', 'content': clean_response})
            logger.debug("AI message added to chat history.")

        # Handle each detected code block
        for match in matches:
            language = match[0] if match[0] else 'text'
            code = match[1]
            logger.info("Code block found (%s): %s", language, code)

            # Display the code block in a separate window
            show_code_window(code, language)
            logger.debug("Code block displayed in separate window.")

            # Optionally, add the code block to chat history if desired
            # Uncomment the following lines if you want code blocks to appear in the chat history
            # formatted_code = f"**Code ({language}):**\n```{language}\n{code}\n```"
            # self.display_ai_message(formatted_code)
            # add_to_chat_history(self.current_chat_id, self.chats, {'role': 'assistant', 'content': formatted_code})

        # Save the chat log
        save_chat_log(self.current_chat_id, self.chats[self.current_chat_id])
        logger.debug("Chat log saved for chat_id '%s'.", self.current_chat_id)

        # Update status to show completion
        agent_config = self.config.get_agent_config('developer')
        status_message = "Response received"
        if agent_config['enabled']:
            agent_name = agent_config['profile'].get('name', 'Agent')
            status_message += f" from {agent_name}"
        self.update_status_message(status_message, is_agent_message=True)
        logger.debug("Status message updated to '%s'.", status_message)

    def handle_ai_error(self, error_message):
        """
        Handle any errors that occur during AI processing.

        Args:
            error_message (str): The error message.
        """
        logger.error("AI Error occurred: %s", error_message)
        QMessageBox.critical(self, "AI Error", f"An error occurred: {error_message}")

    def handle_code_blocks(self, code_blocks):
        """
        Handle code blocks found in the AI's response.

        Args:
            code_blocks (list): List of code blocks.
        """
        logger.debug("Handling code blocks: %s", code_blocks)
        for code_block in code_blocks:
            language = code_block['language']
            code = code_block['code']
            logger.info("Code block found (%s): %s", language, code)

            # Display the code block in a separate window
            show_code_window(code, language)
            logger.debug("Code block displayed in separate window.")

    def display_user_message(self, message):
        """
        Display the user's message in the chat display.
        Minimize code blocks by default.

        Args:
            message (str): The user's message.
        """
        logger.debug("Displaying user message: '%s'", message)
        # Detect code blocks
        code_block_pattern = r'```(\w+)?\n([\s\S]*?)\n```'
        matches = re.findall(code_block_pattern, message)
        logger.debug("Code blocks detected in user message: %s", matches)

        if matches:
            # Split message into text and code blocks
            parts = re.split(code_block_pattern, message)
            formatted_message = ""
            for i in range(len(parts)):
                if i % 3 == 0:
                    # Regular text
                    formatted_message += parts[i] + "\n\n"
                else:
                    # Code block
                    language = parts[i]
                    code = parts[i+1]
                    # Add code block with collapsible syntax
                    formatted_message += f"**User:** [Code Block ({language})](#)\n"
                    formatted_message += f"""<details>
<summary>Click to expand/collapse</summary>
```{language}
{code}
```
</details>
"""
                    formatted_message += "\n\n"
                    # Store code block in Code Blocks tab
                    self.add_code_block(code, language)
                    break  # Assuming one code block per message
            self.append_markdown(formatted_message)
        else:
            formatted_message = f"**User:** {message}"
            self.append_markdown(formatted_message)

    def display_ai_message(self, message):
        """
        Display the AI's message in the chat display.

        Args:
            message (str): The AI's message.
        """
        logger.debug("Displaying AI message: '%s'", message)
        formatted_message = f"**AI:** {message}"
        self.append_markdown(formatted_message)

    def append_markdown(self, message):
        """
        Append a Markdown-formatted message to the chat display.

        Args:
            message (str): The Markdown-formatted message.
        """
        logger.debug("Appending Markdown message: '%s'", message)
        # Get current content
        current_content = self.chat_display.toPlainText()
        # Combine with new message
        new_content = f"{current_content}\n\n{message}"
        # Set the combined content with collapsible support
        self.chat_display.setMarkdown(new_content)
        logger.debug("Markdown message appended to chat display.")

    def update_token_counter(self):
        """
        Update the token counter label based on the content of the user message.
        """
        content = self.user_message_textedit.toPlainText()
        token_count = count_tokens_in_string(content)
        self.token_count_label.setText(f"Tokens: {token_count}")
        logger.debug(f"Token counter updated: {token_count} tokens.")

    def eventFilter(self, source, event):
        """
        Event filter to handle key events for auto-suggesting files and sending messages.

        Args:
            source: The source widget.
            event: The event object.
        """
        if event.type() == QEvent.KeyPress and source is self.user_message_textedit:
            if event.key() == Qt.Key_At:
                QTimer.singleShot(100, self.show_file_suggestions)
                logger.debug("At (@) key pressed in user message text edit. Showing file suggestions.")
                return True
            elif event.key() in (Qt.Key_Return, Qt.Key_Enter):  # Handle both Enter and Keypad Enter
                modifiers = event.modifiers()
                if modifiers & Qt.ShiftModifier:
                    # Insert a new line without sending the message
                    cursor = self.user_message_textedit.textCursor()
                    cursor.insertText('\n')
                    self.user_message_textedit.setTextCursor(cursor)
                    logger.debug("Shift+Enter pressed. New line inserted.")
                    return True
                else:
                    # Send the message if not Shift+Enter
                    logger.debug("Enter pressed. Sending message.")
                    self.send_message()
                    return True
        return super().eventFilter(source, event)

    def show_file_suggestions(self):
        """
        Show a context menu with file suggestions from the datamemory folder.
        """
        logger.debug("Showing file suggestions.")
        show_file_suggestions(self.user_message_textedit)

    def insert_file_name(self, file_name):
        """
        Insert the selected file name into the user message.

        Args:
            file_name (str): The file name to insert.
        """
        logger.debug("Inserting file name into user message: '%s'", file_name)
        insert_file_name(self.user_message_textedit, file_name)

    def update_model(self, model_name):
        """
        Update the AI model based on the selected model.

        Args:
            model_name (str): The name of the selected model.
        """
        logger.debug("Updating model to '%s'.", model_name)
        self.current_model_name = model_name
        try:
            llm = get_model(model_name)
            self.ai_service.update_model(model_name, llm=llm, temperature=self.temperature)
            logger.info("AI model updated to '%s'.", model_name)
        except ValueError as e:
            logger.error("Model update failed: %s", e)
            QMessageBox.critical(self, "Model Error", str(e))

    def update_temperature_from_slider(self, value):
        """
        Update the temperature value when the slider is moved.
        """
        temperature = value / 100
        logger.debug("Temperature slider moved to %d, updating temperature to %.2f.", value, temperature)
        self.temperature_spinbox.blockSignals(True)
        self.temperature_spinbox.setValue(temperature)
        self.temperature_spinbox.blockSignals(False)
        self.update_temperature(temperature)
        self.temperature_spinbox.setToolTip(f"Temperature: {temperature} (Controls randomness)")

    def update_temperature_from_spinbox(self, value):
        """
        Update the temperature value when the spinbox is changed.
        """
        temperature = value
        slider_value = int(value * 100)
        logger.debug("Temperature spinbox changed to %.2f, updating slider to %d.", temperature, slider_value)
        self.temperature_slider.blockSignals(True)
        self.temperature_slider.setValue(slider_value)
        self.temperature_slider.blockSignals(False)
        self.update_temperature(temperature)
        self.temperature_spinbox.setToolTip(f"Temperature: {temperature} (Controls randomness)")

    def update_temperature(self, temperature):
        """
        Update the temperature value.

        Args:
            temperature (float): The new temperature value.
        """
        logger.debug("Updating temperature to %.2f.", temperature)
        self.temperature = temperature
        self.config.CHAT_TEMPERATURE = temperature
        try:
            llm = get_model(self.current_model_name, temperature=temperature)
            self.ai_service.update_model(self.current_model_name, temperature=temperature)
            logger.info("Temperature updated to %.2f and AI model refreshed.", temperature)
        except ValueError as e:
            logger.error("Failed to update temperature: %s", e)
            QMessageBox.critical(self, "Model Error", str(e))

    def update_max_tokens_from_slider(self, value):
        """
        Update the max tokens value when the slider is moved.
        """
        logger.debug("Max tokens slider moved to %d.", value)
        self.max_tokens = value
        self.max_tokens_spinbox.blockSignals(True)
        self.max_tokens_spinbox.setValue(value)
        self.max_tokens_spinbox.blockSignals(False)
        self.update_max_tokens(value)
        self.max_tokens_spinbox.setToolTip(f"Max Tokens: {self.max_tokens}")

    def update_max_tokens_from_spinbox(self, value):
        """
        Update the max tokens value when the spinbox is changed.
        """
        logger.debug("Max tokens spinbox changed to %d.", value)
        self.max_tokens = value
        self.max_tokens_slider.blockSignals(True)
        self.max_tokens_slider.setValue(value)
        self.max_tokens_slider.blockSignals(False)
        self.update_max_tokens(value)
        self.max_tokens_spinbox.setToolTip(f"Max Tokens: {self.max_tokens}")

    def update_max_tokens(self, value):
        """
        Update the max tokens value.
        
        Args:
            value (int): The new max tokens value.
        """
        logger.debug("Updating max tokens to %d.", value)
        self.max_tokens = value
        self.config.MAX_TOKENS = value  # Ensure Config has MAX_TOKENS attribute
        try:
            self.ai_service.update_model(self.current_model_name, temperature=self.temperature)
            logger.info("Max tokens updated to %d and AI model refreshed.", value)
        except ValueError as e:
            logger.error("Failed to update max tokens: %s", e)
            QMessageBox.critical(self, "Model Error", str(e))

    def start_new_chat(self):
        """
        Start a new chat session.
        """
        logger.debug("Starting a new chat session.")
        self.current_chat_id = start_new_chat(self.chats, self.chat_history_list, self.chat_display)
        self.chat_history_content = []
        self.chat_display.setMarkdown("")
        logger.info("New chat session started with chat_id '%s'.", self.current_chat_id)

    def switch_chat(self, item):
        """
        Switch to a selected chat session.
        """
        chat_id = item.data(Qt.UserRole)
        logger.debug("Switching to chat_id '%s'.", chat_id)
        messages = switch_chat(chat_id, self.chats, self.chat_display)
        self.current_chat_id = chat_id
        self.chat_history_content = []
        self.chat_display.setMarkdown("")
        logger.debug("Displaying messages from chat_id '%s'.", chat_id)
        for message in messages:
            if message['role'] == 'user':
                self.display_user_message(message['content'])
                logger.debug("Displayed user message: '%s'", message['content'])
            else:
                self.display_ai_message(message['content'])
                logger.debug("Displayed AI message: '%s'", message['content'])

    def load_selected_chat(self):
        """
        Load the selected chat from chat history.
        """
        logger.debug("Loading selected chat.")
        item = self.chat_history_list.currentItem()
        if item:
            self.switch_chat(item)
            logger.info("Selected chat loaded successfully.")
        else:
            logger.warning("No chat selected to load.")
            QMessageBox.warning(self, "No Chat Selected", "Please select a chat to load.")

    def rename_selected_chat(self):
        """
        Rename the selected chat in the chat history.
        """
        logger.debug("Renaming selected chat.")
        rename_selected_chat(self.chat_history_list, self.chats)
        logger.info("Selected chat renamed.")

    def delete_selected_chat(self):
        """
        Delete the selected chat from the chat history.
        """
        logger.debug("Deleting selected chat.")
        success = delete_selected_chat(self.chat_history_list, self.chats)
        if success:
            self.chat_display.setMarkdown("")
            self.current_chat_id = None
            logger.info("Selected chat deleted successfully.")
        else:
            logger.warning("Failed to delete selected chat.")

    def clear_chat(self):
        """
        Clear the current chat history.
        """
        logger.debug("Clearing current chat.")
        if self.current_chat_id:
            self.chats[self.current_chat_id]['messages'] = []
            self.chat_display.setMarkdown("")
            save_chat_log(self.current_chat_id, self.chats[self.current_chat_id])
            logger.info("Chat history cleared for chat_id '%s'.", self.current_chat_id)
        else:
            logger.warning("No active chat to clear.")
            QMessageBox.warning(self, "No Chat Selected", "No chat session is currently active.")

    def load_chat_history(self):
        """
        Load chat history files into the chat history list.
        """
        logger.debug("Loading chat history.")
        load_chat_history(self.chat_history_list)
        logger.info("Chat history loaded.")

    def update_theme(self, theme_name):
        """
        Update the theme of this page.

        Args:
            theme_name (str): The name of the new theme.
        """
        logger.debug("Updating theme to '%s'.", theme_name)
        apply_theme(self, theme_name)
        # Update code block styles
        code_block_styles = ThemeManager.get_theme().get('CODE_BLOCK_STYLE', {})
        self.chat_display.apply_styles(code_block_styles)
        logger.info("Theme '%s' updated and code block styles applied.", theme_name)

    def on_load(self):
        """
        Called when the page is displayed.
        """
        logger.debug("Page loaded.")
        pass

    def on_unload(self):
        """
        Called when the page is hidden.
        """
        logger.debug("Page unloaded.")
        pass

    def upload_file(self):
        """
        Upload a file to the datamemory folder.
        """
        logger.debug("Uploading file.")
        upload_file(self)

    def view_files(self):
        """
        View files in the datamemory folder.
        """
        logger.debug("Viewing files.")
        view_files(self)

    def browse_input_directory(self):
        """
        Browse and select the input directory.
        """
        logger.debug("Browsing for input directory.")
        directory = QFileDialog.getExistingDirectory(self, "Select Input Directory")
        if directory:
            self.input_dir_lineedit.setText(directory)
            logger.info("Input directory selected: '%s'.", directory)

    def browse_output_directory(self):
        """
        Browse and select the output directory.
        """
        logger.debug("Browsing for output directory.")
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_lineedit.setText(directory)
            logger.info("Output directory selected: '%s'.", directory)

    # --- Code Analysis Methods ---
    def start_code_analysis(self):
        """
        Start the code analysis process in a separate thread.
        """
        logger.debug("Starting code analysis.")
        input_dir = self.input_dir_lineedit.text()
        output_dir = self.output_dir_lineedit.text()
        extensions = self.extensions_lineedit.text()
        system_prompt = self.system_prompt_analysis_textedit.toPlainText()

        logger.debug("Code analysis parameters - Input: '%s', Output: '%s', Extensions: '%s'",
                     input_dir, output_dir, extensions)

        if not input_dir or not output_dir:
            logger.warning("Input or Output directory not specified.")
            QMessageBox.warning(self, "Input Error", "Please specify both input and output directories.")
            return

        # Disable the start button and enable the stop button
        self.start_processing_button.setEnabled(False)
        self.stop_processing_button.setEnabled(True)  # Enable Stop button
        logger.debug("Start button disabled and Stop button enabled.")

        # Show the progress bar and processing log
        self.progress_bar.setVisible(True)
        self.processing_log.setVisible(True)
        self.progress_bar.setValue(0)
        self.processing_log.clear()
        logger.debug("Progress bar and processing log made visible and reset.")

        # Get the selected model
        try:
            llm = get_model(self.current_model_name)
            logger.debug("LLM model '%s' retrieved successfully for code analysis.", self.current_model_name)
        except ValueError as e:
            logger.error("Model retrieval failed: %s", e)
            QMessageBox.critical(self, "Model Error", str(e))
            self.start_processing_button.setEnabled(True)
            self.stop_processing_button.setEnabled(False)  # Disable Stop button
            return

        # Create a QThread
        self.thread = QThread()
        self.worker = Worker(input_dir, output_dir, system_prompt, llm)
        self.worker.moveToThread(self.thread)
        logger.debug("Worker moved to new thread.")

        # Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.processing_finished.connect(self.on_processing_finished)
        self.worker.processing_finished.connect(self.thread.quit)
        self.worker.processing_finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Start the thread
        self.thread.start()
        logger.info("Code analysis thread started.")

    def stop_processing_files(self):
        """
        Stop the ongoing processing of Markdown files.
        """
        logger.debug("Stopping file processing.")
        if hasattr(self, 'worker') and self.worker is not None:
            self.worker.stop()
            self.processing_log.append("Stopping processing...")
            self.stop_processing_button.setEnabled(False)  # Disable Stop button to prevent multiple clicks
            logger.info("Stop processing requested.")
        else:
            logger.warning("No processing task is currently running.")
            QMessageBox.warning(self, "No Processing Task", "There is no processing task to stop.")
