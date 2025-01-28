# ./frontend/pages/qframes/chat/ai_chats_files_processing.py


from typing import Optional, Dict, List, Tuple
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QFileDialog,
    QMessageBox, QTabWidget, QWidget, QTextEdit,
    QProgressBar, QLineEdit, QListWidgetItem
)

# Chat manager imports
from ai_agent.chat_manager.chat_manager import (
    load_chat_history, start_new_chat, switch_chat,
    rename_selected_chat, delete_selected_chat, save_chat_log,
    upload_file, view_files
)

# Processing related imports
from Utils.llm_util.llm_sorted_func import (
    process_files,
    process_file,
    process_function,
    get_md_files,
    parse_markdown_functions,
    get_function_description,
    format_output
)

# Configuration and utilities
from Config.AppConfig.icon_config import ICONS
from log.logger import logger
from ai_agent.models.models import get_model
from ai_agent.config.ai_config import Config
from ..helper.workers import ProcessingWorker

class AIChatFilesProcessing(QFrame):
    """
    A QFrame that contains tabs for chat history, file management, and processing.
    Handles all functionality related to chat management, file operations, and batch processing.
    """
    # Define signals
    chatSelected = Signal(str)
    chatStarted = Signal(str)
    chatRenamed = Signal(str, str)
    chatDeleted = Signal(str)
    chatCleared = Signal(str)
    fileUploaded = Signal(str)
    processingStarted = Signal()
    processingFinished = Signal()
    stateChanged = Signal(dict)
    progressUpdated = Signal(int)
    statusUpdated = Signal(str)
    
    def __init__(self, parent=None):
        """Initialize the left menu frame."""
        super().__init__(parent)
        self.parent = parent
        self.worker = None
        self.thread = None
        self.current_model_name = None
        self.llm = None
        
        # Set frame properties
        self.setObjectName("leftMenuFrame")
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        
        self._init_ui()
        self._setup_connections()
        self.load_state()

    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.West)
        self.tab_widget.setObjectName("leftMenuTabs")

        # Initialize tabs
        self._init_chat_history_tab()
        self._init_file_management_tab()
        self._init_processing_tab()

        # Add tabs
        self.tab_widget.addTab(self.chat_history_tab, "Chats")
        self.tab_widget.addTab(self.file_management_tab, "Files")
        self.tab_widget.addTab(self.processing_tab, "Processing")

        layout.addWidget(self.tab_widget)

    def _init_chat_history_tab(self):
        """Initialize the Chat History tab."""
        self.chat_history_tab = QWidget()
        layout = QVBoxLayout(self.chat_history_tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Title
        chat_history_title = QLabel("Chat History")
        chat_history_title.setAlignment(Qt.AlignCenter)
        chat_history_title.setObjectName("chatHistoryTitle")
        layout.addWidget(chat_history_title)

        # Chat list
        self.chat_history_list = QListWidget()
        self.chat_history_list.setObjectName("chatHistoryList")
        layout.addWidget(self.chat_history_list)

        # Chat management buttons
        self.load_chat_button = QPushButton("Load Selected Chat")
        self.new_chat_button = QPushButton("New Chat")
        self.rename_chat_button = QPushButton("Rename Selected Chat")
        self.delete_chat_button = QPushButton("Delete Selected Chat")
        self.clear_chat_button = QPushButton("Clear Chat")

        # Set object names for styling
        for button, name in [
            (self.load_chat_button, "loadChatButton"),
            (self.new_chat_button, "newChatButton"),
            (self.rename_chat_button, "renameChatButton"),
            (self.delete_chat_button, "deleteChatButton"),
            (self.clear_chat_button, "clearChatButton")
        ]:
            button.setObjectName(name)
            layout.addWidget(button)

        # Load existing chat history
        self.load_chat_history()

    def _init_file_management_tab(self):
        """Initialize the File Management tab."""
        self.file_management_tab = QWidget()
        layout = QVBoxLayout(self.file_management_tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Title
        file_management_title = QLabel("File Management")
        file_management_title.setAlignment(Qt.AlignCenter)
        file_management_title.setObjectName("fileManagementTitle")
        layout.addWidget(file_management_title)

        # File management buttons
        self.upload_file_button = QPushButton("Upload File")
        self.upload_file_button.setIcon(QIcon(ICONS.get('upload', '')))
        self.upload_file_button.setObjectName("uploadFileButton")

        self.view_files_button = QPushButton("View Files")
        self.view_files_button.setIcon(QIcon(ICONS.get('view', '')))
        self.view_files_button.setObjectName("viewFilesButton")

        layout.addWidget(self.upload_file_button)
        layout.addWidget(self.view_files_button)
        layout.addStretch()

    def _init_processing_tab(self):
        """Initialize the Processing tab."""
        self.processing_tab = QWidget()
        layout = QVBoxLayout(self.processing_tab)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Input Directory Section
        input_dir_layout = QHBoxLayout()
        input_dir_label = QLabel("Input Directory:")
        self.input_dir_lineedit = QLineEdit()
        self.input_dir_browse_button = QPushButton("Browse")
        self.input_dir_browse_button.clicked.connect(self._browse_input_directory)
        
        input_dir_layout.addWidget(input_dir_label)
        input_dir_layout.addWidget(self.input_dir_lineedit)
        input_dir_layout.addWidget(self.input_dir_browse_button)
        layout.addLayout(input_dir_layout)

        # Output Directory Section
        output_dir_layout = QHBoxLayout()
        output_dir_label = QLabel("Output Directory:")
        self.output_dir_lineedit = QLineEdit()
        self.output_dir_browse_button = QPushButton("Browse")
        self.output_dir_browse_button.clicked.connect(self._browse_output_directory)
        
        output_dir_layout.addWidget(output_dir_label)
        output_dir_layout.addWidget(self.output_dir_lineedit)
        output_dir_layout.addWidget(self.output_dir_browse_button)
        layout.addLayout(output_dir_layout)

        # System Prompt Section
        system_prompt_label = QLabel("System Prompt:")
        self.system_prompt_textedit = QTextEdit()
        layout.addWidget(system_prompt_label)
        layout.addWidget(self.system_prompt_textedit)

        # Processing buttons
        self.start_processing_button = QPushButton("Process Files")
        self.start_processing_button.setIcon(QIcon(ICONS.get('process', '')))
        self.start_processing_button.setObjectName("startProcessingButton")

        self.stop_processing_button = QPushButton("Stop Processing")
        self.stop_processing_button.setIcon(QIcon(ICONS.get('stop', '')))
        self.stop_processing_button.setEnabled(False)
        self.stop_processing_button.setObjectName("stopProcessingButton")

        layout.addWidget(self.start_processing_button)
        layout.addWidget(self.stop_processing_button)

        # Progress tracking
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setObjectName("processingProgressBar")
        layout.addWidget(self.progress_bar)

        # Processing log
        self.processing_log = QTextEdit()
        self.processing_log.setReadOnly(True)
        self.processing_log.setVisible(False)
        self.processing_log.setObjectName("processingLog")
        layout.addWidget(self.processing_log)

        layout.addStretch()

    def _setup_connections(self) -> None:
        """Connect all signals to their slots."""
        # Chat management
        self.new_chat_button.clicked.connect(self._handle_new_chat)
        self.load_chat_button.clicked.connect(self._handle_load_chat)
        self.rename_chat_button.clicked.connect(self._handle_rename_chat)
        self.delete_chat_button.clicked.connect(self._handle_delete_chat)
        self.clear_chat_button.clicked.connect(self._handle_clear_chat)
        self.chat_history_list.itemClicked.connect(self._handle_chat_selected)

        # File management
        self.upload_file_button.clicked.connect(self._handle_upload_file)
        self.view_files_button.clicked.connect(self._handle_view_files)

        # Processing
        self.start_processing_button.clicked.connect(self._handle_start_processing)
        self.stop_processing_button.clicked.connect(self._handle_stop_processing)

    def _browse_input_directory(self) -> None:
        """Open dialog to browse for input directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Input Directory",
            self.input_dir_lineedit.text()
        )
        if directory:
            self.input_dir_lineedit.setText(directory)
            self.save_state()

    def _browse_output_directory(self) -> None:
        """Open dialog to browse for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory",
            self.output_dir_lineedit.text()
        )
        if directory:
            self.output_dir_lineedit.setText(directory)
            self.save_state()

    def load_chat_history(self) -> None:
        """Load existing chat history."""
        try:
            load_chat_history(self.chat_history_list)
        except Exception as e:
            logger.error(f"Error loading chat history: {str(e)}")
            self._show_error("Error", "Failed to load chat history.")

    def _handle_new_chat(self) -> None:
        """Handle creating a new chat."""
        try:
            chat_id = start_new_chat({}, self.chat_history_list, None)
            self.chatStarted.emit(chat_id)
        except Exception as e:
            logger.error(f"Error creating new chat: {str(e)}")
            self._show_error("Error", "Failed to create new chat.")

    def _handle_load_chat(self) -> None:
        """Handle loading selected chat."""
        item = self.chat_history_list.currentItem()
        if item:
            try:
                chat_id = item.data(Qt.UserRole)
                self.chatSelected.emit(chat_id)
            except Exception as e:
                logger.error(f"Error loading chat: {str(e)}")
                self._show_error("Error", "Failed to load chat.")
        else:
            QMessageBox.warning(self, "No Selection", "Please select a chat to load.")

    def _handle_rename_chat(self) -> None:
        """Handle renaming selected chat."""
        try:
            success, old_id, new_id = rename_selected_chat(self.chat_history_list, {})
            if success:
                self.chatRenamed.emit(old_id, new_id)
                self.save_state()
        except Exception as e:
            logger.error(f"Error renaming chat: {str(e)}")
            self._show_error("Error", "Failed to rename chat.")

    def _handle_delete_chat(self) -> None:
        """Handle deleting selected chat."""
        item = self.chat_history_list.currentItem()
        if item:
            try:
                chat_id = item.data(Qt.UserRole)
                if delete_selected_chat(self.chat_history_list, {}):
                    self.chatDeleted.emit(chat_id)
                    self.save_state()
            except Exception as e:
                logger.error(f"Error deleting chat: {str(e)}")
                self._show_error("Error", "Failed to delete chat.")

    def _handle_clear_chat(self) -> None:
        """Handle clearing current chat."""
        item = self.chat_history_list.currentItem()
        if item:
            try:
                chat_id = item.data(Qt.UserRole)
                self.chatCleared.emit(chat_id)
                self.save_state()
            except Exception as e:
                logger.error(f"Error clearing chat: {str(e)}")
                self._show_error("Error", "Failed to clear chat.")

    def _handle_chat_selected(self, item: QListWidgetItem) -> None:
        """Handle chat selection."""
        try:
            chat_id = item.data(Qt.UserRole)
            self.chatSelected.emit(chat_id)
            self.save_state()
        except Exception as e:
            logger.error(f"Error selecting chat: {str(e)}")
            self._show_error("Error", "Failed to select chat.")

    def _handle_upload_file(self) -> None:
        """Handle file upload."""
        try:
            file_path = upload_file(self)
            if file_path:
                self.fileUploaded.emit(file_path)
                self.save_state()
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            self._show_error("Upload Error", f"Failed to upload file: {str(e)}")

    def _handle_view_files(self) -> None:
        """Handle viewing files."""
        try:
            view_files(self)
        except Exception as e:
            logger.error(f"Error viewing files: {str(e)}")
            self._show_error("Error", f"Failed to view files: {str(e)}")

    def _handle_start_processing(self) -> None:
        """Start the processing operation."""
        try:
            input_dir = self.input_dir_lineedit.text()
            output_dir = self.output_dir_lineedit.text()
            system_prompt = self.system_prompt_textedit.toPlainText()

            if not all([input_dir, output_dir]):
                QMessageBox.warning(self, "Input Error", 
                                  "Please specify both input and output directories.")
                return

            if not system_prompt:
                QMessageBox.warning(self, "Input Error", 
                                  "System prompt cannot be empty.")
                return

            # Validate input directory contains .md files
            md_files = get_md_files(input_dir)
            if not md_files:
                QMessageBox.warning(self, "Input Error", 
                                  "No markdown files found in input directory.")
                return

            # Get the selected model
            try:
                self.llm = get_model(self.current_model_name)
            except ValueError as e:
                QMessageBox.critical(self, "Model Error", str(e))
                return

            # Create thread and worker
            self.thread = QThread()
            self.worker = ProcessingWorker(
                input_dir=input_dir,
                output_dir=output_dir,
                system_prompt=system_prompt,
                llm=self.llm,
                worker_type="file_processing"
            )
            self.worker.moveToThread(self.thread)

            # Connect signals and slots
            self.thread.started.connect(self.worker.run)
            self.worker.progress_update.connect(self.update_progress_with_processing)
            self.worker.processing_finished.connect(self._on_processing_finished)
            self.worker.processing_finished.connect(self.thread.quit)
            self.worker.processing_finished.connect(self.worker.deleteLater)
            self.worker.error.connect(self._handle_processing_error)
            self.thread.finished.connect(self.thread.deleteLater)

            # Update UI
            self._update_ui_processing_started()

            # Start processing
            self.thread.start()
            self.processingStarted.emit()

        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            self._show_error("Processing Error", str(e))
            self._reset_processing_ui()

    def _handle_stop_processing(self) -> None:
        """Stop the ongoing processing."""
        if hasattr(self, 'worker') and self.worker is not None:
            self.worker.stop()
            self.processing_log.append("Stopping processing...")
            self.stop_processing_button.setEnabled(False)
        else:
            QMessageBox.warning(self, "No Processing Task", 
                              "There is no processing task to stop.")

    def _update_ui_processing_started(self) -> None:
        """Update UI when processing starts."""
        self.start_processing_button.setEnabled(False)
        self.stop_processing_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.processing_log.setVisible(True)
        self.progress_bar.setValue(0)
        self.processing_log.clear()
        self.processing_log.append("Starting processing...")

    def update_progress_with_processing(self, item_name: str, status: str) -> None:
        """Update progress with processing status."""
        self._update_progress(item_name, status)
        progress_value = self.progress_bar.value()
        self.progressUpdated.emit(progress_value)
        self.statusUpdated.emit(f"{item_name}: {status}")

    def _update_progress(self, item_name: str, status: str) -> None:
        """Update the progress display."""
        self.processing_log.append(f"{item_name}: {status}")
        
        if status == "Completed":
            self.progress_bar.setValue(100)
            self.progressUpdated.emit(100)
        else:
            # Increment progress bar
            current_value = self.progress_bar.value()
            if current_value < 95:  # Leave room for completion
                new_value = current_value + 5
                self.progress_bar.setValue(new_value)
                self.progressUpdated.emit(new_value)
        
        self.statusUpdated.emit(f"{item_name}: {status}")
        self.save_state()

    def _on_processing_finished(self) -> None:
        """Handle completion of processing."""
        self._reset_processing_ui()
        self.processing_log.append("\nProcessing completed!")
        self.processingFinished.emit()
        QMessageBox.information(self, "Processing Complete", 
                              "File processing has been completed.")

    def _handle_processing_error(self, error_msg: str) -> None:
        """Handle processing errors."""
        logger.error(f"Processing error: {error_msg}")
        self._show_error("Processing Error", error_msg)
        self._reset_processing_ui()

    def save_state(self) -> None:
        """Save current state to configuration."""
        try:
            state = {
                'current_tab': self.tab_widget.currentIndex(),
                'input_directory': self.input_dir_lineedit.text(),
                'output_directory': self.output_dir_lineedit.text(),
                'system_prompt': self.system_prompt_textedit.toPlainText(),
                'selected_chat': self.get_selected_chat_id(),
                'progress_visible': self.progress_bar.isVisible(),
                'progress_value': self.progress_bar.value(),
                'log_visible': self.processing_log.isVisible(),
                'log_content': self.processing_log.toPlainText()
            }
            self.parent.config.save_left_menu_state(state)
            self.stateChanged.emit(state)
            
        except Exception as e:
            logger.error(f"Error saving state: {str(e)}")
            self._show_error("Save Error", f"Failed to save state: {str(e)}")

    def load_state(self) -> None:
        """Load saved state from configuration."""
        try:
            state = self.parent.config.load_left_menu_state()
            if state:
                if 'current_tab' in state:
                    self.tab_widget.setCurrentIndex(state['current_tab'])
                if 'input_directory' in state:
                    self.input_dir_lineedit.setText(state['input_directory'])
                if 'output_directory' in state:
                    self.output_dir_lineedit.setText(state['output_directory'])
                if 'system_prompt' in state:
                    self.system_prompt_textedit.setText(state['system_prompt'])
                if 'selected_chat' in state and state['selected_chat']:
                    self.select_chat(state['selected_chat'])
                if 'progress_visible' in state:
                    self.progress_bar.setVisible(state['progress_visible'])
                if 'progress_value' in state:
                    self.progress_bar.setValue(state['progress_value'])
                if 'log_visible' in state:
                    self.processing_log.setVisible(state['log_visible'])
                if 'log_content' in state:
                    self.processing_log.setText(state['log_content'])
                    
        except Exception as e:
            logger.error(f"Error loading state: {str(e)}")
            self._show_error("Load Error", f"Failed to load state: {str(e)}")

    def _show_error(self, title: str, message: str) -> None:
        """Show error message to user."""
        logger.error(f"{title}: {message}")
        QMessageBox.critical(self, title, message)

    def reset_processing(self) -> None:
        """Reset all processing related elements."""
        try:
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(False)
            self.processing_log.clear()
            self.processing_log.setVisible(False)
            self.start_processing_button.setEnabled(True)
            self.stop_processing_button.setEnabled(False)
            self.input_dir_lineedit.clear()
            self.output_dir_lineedit.clear()
            self.system_prompt_textedit.clear()
            
        except Exception as e:
            logger.error(f"Error resetting processing: {str(e)}")
            self._show_error("Reset Error", f"Failed to reset processing: {str(e)}")

    def set_model(self, model_name: str) -> None:
        """Set the current model name."""
        self.current_model_name = model_name

    def get_selected_chat_id(self) -> Optional[str]:
        """Get the currently selected chat ID."""
        item = self.chat_history_list.currentItem()
        return item.data(Qt.UserRole) if item else None

    def select_chat(self, chat_id: str) -> None:
        """Select a specific chat in the list."""
        for i in range(self.chat_history_list.count()):
            item = self.chat_history_list.item(i)
            if item.data(Qt.UserRole) == chat_id:
                self.chat_history_list.setCurrentItem(item)
                break

    def handle_parent_close(self) -> None:
        """Handle cleanup when parent is closing."""
        if self.is_processing():
            self._handle_stop_processing()
        self.save_state()

    def is_processing(self) -> bool:
        """Check if processing is currently active."""
        return (self.worker is not None and 
                hasattr(self.worker, '_is_running') and 
                self.worker._is_running)


