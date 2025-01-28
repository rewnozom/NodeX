# ./frontend/pages/qframes/chat/ai_chats_files_processing.py


from typing import Optional, Dict, List, Tuple
from PySide6.QtCore import Qt, Signal, QThread, QPropertyAnimation, QRect
from PySide6.QtGui import QIcon, QSwipeGesture, QGestureEvent
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QFileDialog,
    QMessageBox, QTabWidget, QWidget, QTextEdit,
    QProgressBar, QLineEdit, QListWidgetItem,
    QScrollArea, QGestureRecognizer, QStackedWidget
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

from Config.phone_config.phone_functions import (
    MobileStyles, MobileOptimizations, MobileBottomSheet, ChatBubbleDelegate, apply_mobile_style,
    VoiceInputButton  # Om röstinmatning ska inkluderas
)
from frontend._layout.layout_manager import LayoutManager  # Om behövs

class BottomSheet(QWidget):
    """A mobile-friendly bottom sheet widget that slides up from the bottom."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mobileBottomSheet")
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 10, 0, 0)
        
        # Handle bar for dragging
        handle = QFrame()
        handle.setObjectName("bottomSheetHandle")
        handle.setFixedSize(40, 4)
        handle_layout = QHBoxLayout()
        handle_layout.addWidget(handle)
        handle_layout.setAlignment(Qt.AlignCenter)
        self.layout.addLayout(handle_layout)
        
        # Content area
        self.content = QScrollArea()
        self.content.setWidgetResizable(True)
        self.layout.addWidget(self.content)
        
        self.setStyleSheet("""
            QWidget#mobileBottomSheet {
                background: white;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                box-shadow: 0px -2px 10px rgba(0, 0, 0, 0.1);
            }
            QFrame#bottomSheetHandle {
                background: #E0E0E0;
                border-radius: 2px;
            }
        """)

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
        """Initialize the frame."""
        super().__init__(parent)
        self.parent = parent
        self.worker = None
        self.thread = None
        self.current_model_name = None
        self.llm = None
        self.is_phone_layout = self.parent.config.get('enable_phone_layout', False)
        
        # Set frame properties
        self.setObjectName("chatFilesProcessingFrame")
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        
        # Apply mobile optimizations if in phone layout
        if self.is_phone_layout:
            MobileOptimizations.apply_optimizations(self)
        
        # Initialize UI based on layout type
        if self.is_phone_layout:
            self._init_phone_ui()
        else:
            self._init_desktop_ui()
            
        self._setup_connections()
        self.load_state()
    
    def _init_phone_ui(self):
        """Initialize mobile-optimized UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main content area with chat history
        self.main_content = QWidget()
        main_layout = QVBoxLayout(self.main_content)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Chat list with larger touch targets
        self.chat_history_list = QListWidget()
        self.chat_history_list.setObjectName("mobileChatList")
        self.chat_history_list.setStyleSheet("""
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #E0E0E0;
            }
        """)
        main_layout.addWidget(self.chat_history_list)
        
        # Quick action buttons
        actions_layout = QHBoxLayout()
        
        self.new_chat_button = QPushButton()
        self.new_chat_button.setIcon(QIcon(ICONS.get('plus', '')))
        self.new_chat_button.setToolTip("New Chat")
        self.new_chat_button.setMinimumSize(50, 50)
        self.new_chat_button.setObjectName("mobileActionButton")
        apply_mobile_style(self.new_chat_button, "mobileActionButton")
        
        self.upload_button = QPushButton()
        self.upload_button.setIcon(QIcon(ICONS.get('upload', '')))
        self.upload_button.setToolTip("Upload File")
        self.upload_button.setMinimumSize(50, 50)
        self.upload_button.setObjectName("mobileActionButton")
        apply_mobile_style(self.upload_button, "mobileActionButton")
        
        self.more_options_button = QPushButton()
        self.more_options_button.setIcon(QIcon(ICONS.get('menu', '')))
        self.more_options_button.setToolTip("More Options")
        self.more_options_button.setMinimumSize(50, 50)
        self.more_options_button.setObjectName("mobileActionButton")
        apply_mobile_style(self.more_options_button, "mobileActionButton")
        
        for btn in [self.new_chat_button, self.upload_button, self.more_options_button]:
            actions_layout.addWidget(btn)
            
        main_layout.addLayout(actions_layout)
        
        # Initialize bottom sheets for different functionalities
        self._init_bottom_sheets()
        
        layout.addWidget(self.main_content)
        
        # Style the mobile interface
        self.setStyleSheet("""
            QPushButton#mobileActionButton {
                background-color: #F5F5F5;
                border: none;
                border-radius: 25px;
                padding: 12px;
            }
            QPushButton#mobileActionButton:pressed {
                background-color: #E0E0E0;
            }
        """)
    
    def _init_bottom_sheets(self):
        """Initialize bottom sheets for mobile interface."""
        # Chat options sheet
        self.chat_options_sheet = BottomSheet(self)
        chat_options_content = QWidget()
        chat_options_layout = QVBoxLayout(chat_options_content)
        
        chat_action_buttons = [
            ("Rename Chat", self._handle_rename_chat),
            ("Delete Chat", self._handle_delete_chat),
            ("Clear Chat", self._handle_clear_chat)
        ]
        
        for text, handler in chat_action_buttons:
            btn = QPushButton(text)
            btn.setMinimumHeight(50)
            btn.clicked.connect(handler)
            chat_options_layout.addWidget(btn)
            
        self.chat_options_sheet.content.setWidget(chat_options_content)
        self.chat_options_sheet.hide()
        
        # Processing sheet
        self.processing_sheet = BottomSheet(self)
        processing_content = QWidget()
        processing_layout = QVBoxLayout(processing_content)
        
        # Add processing controls
        self._init_processing_controls(processing_layout)
        self.processing_sheet.content.setWidget(processing_content)
        self.processing_sheet.hide()
    
    def _init_processing_controls(self, layout):
        """Initialize processing controls for mobile interface."""
        # Simplified input fields
        self.input_dir_button = QPushButton("Select Input Directory")
        self.input_dir_button.clicked.connect(self._browse_input_directory)
        self.input_dir_button.setMinimumHeight(50)
        apply_mobile_style(self.input_dir_button, "mobileActionButton")
        
        self.output_dir_button = QPushButton("Select Output Directory")
        self.output_dir_button.clicked.connect(self._browse_output_directory)
        self.output_dir_button.setMinimumHeight(50)
        apply_mobile_style(self.output_dir_button, "mobileActionButton")
        
        # System prompt with expandable text area
        self.system_prompt_textedit = QTextEdit()
        self.system_prompt_textedit.setPlaceholderText("Enter system prompt...")
        self.system_prompt_textedit.setMaximumHeight(100)
        apply_mobile_style(self.system_prompt_textedit, "mobileInput")
        
        # Process button
        self.start_processing_button = QPushButton("Start Processing")
        self.start_processing_button.setMinimumHeight(50)
        self.start_processing_button.setObjectName("mobileProcessButton")
        apply_mobile_style(self.start_processing_button, "mobileProcessButton")
        
        # Progress indicators
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setObjectName("mobileProgressBar")
        
        self.processing_log = QTextEdit()
        self.processing_log.setReadOnly(True)
        self.processing_log.setVisible(False)
        self.processing_log.setMaximumHeight(100)
        apply_mobile_style(self.processing_log, "mobileInput")
        
        # Add all widgets to layout
        for widget in [
            self.input_dir_button,
            self.output_dir_button,
            self.system_prompt_textedit,
            self.start_processing_button,
            self.progress_bar,
            self.processing_log
        ]:
            layout.addWidget(widget)
    
    def _init_desktop_ui(self):
        """Initialize desktop UI."""
        # Main vertical layout
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
    
    def _setup_connections(self) -> None:
        """Connect all signals to their respective slots."""
        if self.is_phone_layout:
            # Chat management
            self.new_chat_button.clicked.connect(self._handle_new_chat)
            self.upload_button.clicked.connect(self._handle_upload_file)
            self.more_options_button.clicked.connect(self._show_chat_options_sheet)
            self.chat_history_list.itemClicked.connect(self._handle_chat_selected)

            # Processing
            self.start_processing_button.clicked.connect(self._handle_start_processing)
            # Stop processing button is inte existerande i mobil UI
        else:
            # Desktop Chat management
            self.new_chat_button.clicked.connect(self._handle_new_chat)
            self.load_chat_button.clicked.connect(self._handle_load_chat)
            self.rename_chat_button.clicked.connect(self._handle_rename_chat)
            self.delete_chat_button.clicked.connect(self._handle_delete_chat)
            self.clear_chat_button.clicked.connect(self._handle_clear_chat)
            self.chat_history_list.itemClicked.connect(self._handle_chat_selected)

            # Desktop File management
            self.upload_file_button.clicked.connect(self._handle_upload_file)
            self.view_files_button.clicked.connect(self._handle_view_files)

            # Desktop Processing
            self.start_processing_button.clicked.connect(self._handle_start_processing)
            self.stop_processing_button.clicked.connect(self._handle_stop_processing)
    
    def _show_chat_options_sheet(self):
        """Show the chat options bottom sheet."""
        self.show_bottom_sheet("chat_options")
    
    def _init_bottom_sheets(self):
        """Initialize bottom sheets for mobile interface."""
        # Chat options sheet
        self.chat_options_sheet = BottomSheet(self)
        chat_options_content = QWidget()
        chat_options_layout = QVBoxLayout(chat_options_content)
        
        chat_action_buttons = [
            ("Rename Chat", self._handle_rename_chat),
            ("Delete Chat", self._handle_delete_chat),
            ("Clear Chat", self._handle_clear_chat)
        ]
        
        for text, handler in chat_action_buttons:
            btn = QPushButton(text)
            btn.setMinimumHeight(50)
            btn.clicked.connect(handler)
            chat_options_layout.addWidget(btn)
            
        self.chat_options_sheet.content.setWidget(chat_options_content)
        self.chat_options_sheet.hide()
        
        # Processing sheet
        self.processing_sheet = BottomSheet(self)
        processing_content = QWidget()
        processing_layout = QVBoxLayout(processing_content)
        
        # Add processing controls
        self._init_processing_controls(processing_layout)
        self.processing_sheet.content.setWidget(processing_content)
        self.processing_sheet.hide()
    
    def show_bottom_sheet(self, sheet_name: str):
        """Show the specified bottom sheet with animation."""
        sheet = getattr(self, f"{sheet_name}_sheet", None)
        if sheet and sheet.isHidden():
            sheet.show()
            animation = QPropertyAnimation(sheet, b"geometry")
            animation.setDuration(300)
            animation.setStartValue(
                QRect(0, self.height(), self.width(), self.height() * 0.7)
            )
            animation.setEndValue(
                QRect(0, self.height() * 0.3, self.width(), self.height() * 0.7)
            )
            animation.start()
    
    def hide_bottom_sheet(self, sheet_name: str):
        """Hide the specified bottom sheet with animation."""
        sheet = getattr(self, f"{sheet_name}_sheet", None)
        if sheet and not sheet.isHidden():
            animation = QPropertyAnimation(sheet, b"geometry")
            animation.setDuration(300)
            animation.setEndValue(
                QRect(0, self.height(), self.width(), self.height() * 0.7)
            )
            animation.finished.connect(sheet.hide)
            animation.start()
    
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
            if self.is_phone_layout:
                # Show processing bottom sheet
                self.show_bottom_sheet("processing")
                input_dir = self.input_dir_button.text()
                output_dir = self.output_dir_button.text()
                system_prompt = self.system_prompt_textedit.toPlainText()
            else:
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
            if self.is_phone_layout:
                self.processing_sheet.progress_bar = self.progress_bar
                self.processing_sheet.processing_log = self.processing_log
            else:
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
                'input_directory': self.input_dir_lineedit.text() if not self.is_phone_layout else self.input_dir_button.text(),
                'output_directory': self.output_dir_lineedit.text() if not self.is_phone_layout else self.output_dir_button.text(),
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
                    if self.is_phone_layout:
                        self.input_dir_button.setText(state['input_directory'])
                    else:
                        self.input_dir_lineedit.setText(state['input_directory'])
                if 'output_directory' in state:
                    if self.is_phone_layout:
                        self.output_dir_button.setText(state['output_directory'])
                    else:
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
            if self.is_phone_layout:
                self.input_dir_button.setText("")
                self.output_dir_button.setText("")
                self.system_prompt_textedit.clear()
            else:
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
    
    def show_bottom_sheet(self, sheet_name: str):
        """Show the specified bottom sheet with animation."""
        sheet = getattr(self, f"{sheet_name}_sheet", None)
        if sheet and sheet.isHidden():
            sheet.show()
            animation = QPropertyAnimation(sheet, b"geometry")
            animation.setDuration(300)
            animation.setStartValue(
                QRect(0, self.height(), self.width(), self.height() * 0.7)
            )
            animation.setEndValue(
                QRect(0, self.height() * 0.3, self.width(), self.height() * 0.7)
            )
            animation.start()
    
    def hide_bottom_sheet(self, sheet_name: str):
        """Hide the specified bottom sheet with animation."""
        sheet = getattr(self, f"{sheet_name}_sheet", None)
        if sheet and not sheet.isHidden():
            animation = QPropertyAnimation(sheet, b"geometry")
            animation.setDuration(300)
            animation.setEndValue(
                QRect(0, self.height(), self.width(), self.height() * 0.7)
            )
            animation.finished.connect(sheet.hide)
            animation.start()
    
    # (Valfritt) Hantera röstinmatning
    def _handle_voice_input(self, text: str):
        """Handle voice input transcription."""
        self.system_prompt_textedit.setPlainText(text)
