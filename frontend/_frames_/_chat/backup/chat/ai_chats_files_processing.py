# ./frontend/pages/qframes/chat/ai_chats_files_processing.py


from PySide6.QtCore import Qt, Signal, QObject, QThread
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QFileDialog,
    QMessageBox, QTabWidget, QWidget, QTextEdit,
    QProgressBar
)

from ai_agent.chat_manager.chat_manager import (
    load_chat_history, start_new_chat, switch_chat,
    rename_selected_chat, delete_selected_chat, save_chat_log,
    upload_file, view_files
)
from ai_agent.utils.helpers import process_files
from Config.AppConfig.icon_config import ICONS
from log.logger import logger
from frontend._frames_._helper.workers import FileProcessingWorker  # New import

def _handle_start_processing(self):
    try:
        # Create thread and worker
        self.thread = QThread()
        self.worker = FileProcessingWorker(
            input_dir=self.input_dir_lineedit.text(),
            output_dir=self.output_dir_lineedit.text(),
            system_prompt=self.system_prompt_textedit.toPlainText(),
            llm=self.llm
        )
        self.worker.moveToThread(self.thread)

        # Connect signals and slots
        self.thread.started.connect(self.worker.run)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.processing_finished.connect(self.on_processing_finished)
        self.worker.processing_finished.connect(self.thread.quit)
        self.worker.processing_finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self._handle_processing_error)  # New error handling
        self.thread.finished.connect(self.thread.deleteLater)

        # Update UI
        self.start_processing_button.setEnabled(False)
        self.stop_processing_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.processing_log.setVisible(True)
        self.progress_bar.setValue(0)
        self.processing_log.clear()

        # Start the thread
        self.thread.start()

    except Exception as e:
        QMessageBox.critical(self, "Processing Error", str(e))
        self._reset_processing_ui()

def _handle_processing_error(self, error_msg):
    """Handle processing errors."""
    QMessageBox.critical(self, "Processing Error", error_msg)
    self._reset_processing_ui()

def _reset_processing_ui(self):
    """Reset UI elements after processing ends or errors."""
    self.start_processing_button.setEnabled(True)
    self.stop_processing_button.setEnabled(False)
    self.progress_bar.setValue(0)

class AIChatFilesProcessing(QFrame):
    """
    A QFrame that contains tabs for chat history, file management, and processing.
    Handles all functionality related to chat management, file operations, and batch processing.
    """

    # Define signals
    chatSelected = Signal(str)  # Emitted when a chat is selected
    chatStarted = Signal(str)   # Emitted when a new chat is started
    chatRenamed = Signal(str, str)  # Emitted when a chat is renamed (old_id, new_id)
    chatDeleted = Signal(str)   # Emitted when a chat is deleted
    chatCleared = Signal(str)   # Emitted when a chat is cleared
    fileUploaded = Signal(str)  # Emitted when a file is uploaded
    processingStarted = Signal()  # Emitted when processing starts
    processingFinished = Signal()  # Emitted when processing finishes
    
    def __init__(self, parent=None):
        """Initialize the left menu frame."""
        super().__init__(parent)
        self.parent = parent
        self.worker = None
        self.thread = None
        
        # Set frame properties
        self.setObjectName("leftMenuFrame")
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        
        self._init_ui()
        self._setup_connections()

    def _init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.West)  # Tabs on the left
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
        self.load_chat_button.setObjectName("loadChatButton")
        
        self.new_chat_button = QPushButton("New Chat")
        self.new_chat_button.setObjectName("newChatButton")
        
        self.rename_chat_button = QPushButton("Rename Selected Chat")
        self.rename_chat_button.setObjectName("renameChatButton")
        
        self.delete_chat_button = QPushButton("Delete Selected Chat")
        self.delete_chat_button.setObjectName("deleteChatButton")
        
        self.clear_chat_button = QPushButton("Clear Chat")
        self.clear_chat_button.setObjectName("clearChatButton")

        for button in [
            self.load_chat_button, self.new_chat_button,
            self.rename_chat_button, self.delete_chat_button,
            self.clear_chat_button
        ]:
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

    def _setup_connections(self):
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

    def load_chat_history(self):
        """Load existing chat history."""
        try:
            load_chat_history(self.chat_history_list)
        except Exception as e:
            logger.error(f"Error loading chat history: {str(e)}")
            QMessageBox.warning(self, "Error", "Failed to load chat history.")

    def _handle_new_chat(self):
        """Handle creating a new chat."""
        chat_id = start_new_chat({}, self.chat_history_list, None)
        self.chatStarted.emit(chat_id)

    def _handle_load_chat(self):
        """Handle loading selected chat."""
        item = self.chat_history_list.currentItem()
        if item:
            chat_id = item.data(Qt.UserRole)
            self.chatSelected.emit(chat_id)
        else:
            QMessageBox.warning(self, "No Selection", "Please select a chat to load.")

    def _handle_rename_chat(self):
        """Handle renaming selected chat."""
        success, old_id, new_id = rename_selected_chat(self.chat_history_list, {})
        if success:
            self.chatRenamed.emit(old_id, new_id)

    def _handle_delete_chat(self):
        """Handle deleting selected chat."""
        item = self.chat_history_list.currentItem()
        if item:
            chat_id = item.data(Qt.UserRole)
            if delete_selected_chat(self.chat_history_list, {}):
                self.chatDeleted.emit(chat_id)

    def _handle_clear_chat(self):
        """Handle clearing current chat."""
        item = self.chat_history_list.currentItem()
        if item:
            chat_id = item.data(Qt.UserRole)
            self.chatCleared.emit(chat_id)

    def _handle_chat_selected(self, item):
        """Handle chat selection."""
        chat_id = item.data(Qt.UserRole)
        self.chatSelected.emit(chat_id)

    def _handle_upload_file(self):
        """Handle file upload."""
        try:
            file_path = upload_file(self)
            if file_path:
                self.fileUploaded.emit(file_path)
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            QMessageBox.warning(self, "Upload Error", f"Failed to upload file: {str(e)}")

    def _handle_view_files(self):
        """Handle viewing files."""
        try:
            view_files(self)
        except Exception as e:
            logger.error(f"Error viewing files: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to view files: {str(e)}")

    def _handle_start_processing(self):
        """Start the processing operation."""
        self.processingStarted.emit()
        self.progress_bar.setVisible(True)
        self.processing_log.setVisible(True)
        self.progress_bar.setValue(0)
        self.processing_log.clear()
        
        self.start_processing_button.setEnabled(False)
        self.stop_processing_button.setEnabled(True)

    def _handle_stop_processing(self):
        """Stop the processing operation."""
        if self.worker:
            self.worker.stop()
            self.stop_processing_button.setEnabled(False)
            self.processing_log.append("Stopping processing...")

    def update_processing_progress(self, item_name, status):
        """Update the processing progress display."""
        self.processing_log.append(f"{item_name}: {status}")
        if status == "Completed":
            self.progress_bar.setValue(100)
            self.start_processing_button.setEnabled(True)
            self.stop_processing_button.setEnabled(False)
            self.processingFinished.emit()

    def get_selected_chat_id(self):
        """Get the currently selected chat ID."""
        item = self.chat_history_list.currentItem()
        return item.data(Qt.UserRole) if item else None

    def select_chat(self, chat_id):
        """Select a specific chat in the list."""
        for i in range(self.chat_history_list.count()):
            item = self.chat_history_list.item(i)
            if item.data(Qt.UserRole) == chat_id:
                self.chat_history_list.setCurrentItem(item)
                break