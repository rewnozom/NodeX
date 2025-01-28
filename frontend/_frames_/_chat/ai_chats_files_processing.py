# ./frontend/pages/qframes/chat/ai_chats_files_processing.py

from typing import Optional, Dict, List, Tuple
from PySide6.QtCore import Qt, Signal, QThread, QPropertyAnimation, QRect, QEasingCurve
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QFileDialog, QSwipeGesture, QGestureEvent,
    QMessageBox, QTabWidget, QWidget, QTextEdit,
    QProgressBar, QLineEdit, QListWidgetItem,
    QScrollArea, QGestureRecognizer, QStackedWidget
)
from ai_agent.config.prompt_manager import (
    load_specific_system_prompt, save_system_prompt
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
from .._helper.workers import ProcessingWorker

from Config.phone_config.phone_functions import (
    MobileStyles, MobileOptimizations, MobileBottomSheet, ChatBubbleDelegate, apply_mobile_style,
    VoiceInputButton  # Om röstinmatning ska inkluderas
)
from frontend._layout.layout_manager import LayoutManager  # Om behövs

# Import CodeAnalysis
from .code_analysis import CodeAnalysis


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
    
    # New signal for analysis requests
    analysisRequested = Signal(dict)
    
    def __init__(self, parent=None):
        """Initialize the frame."""
        super().__init__(parent)
        self.parent = parent
        self.worker = None
        self.thread = None
        self.current_model_name = None
        self.llm = None
        self.is_phone_layout = getattr(self.parent, 'config', {}).get('enable_phone_layout', False)

        # Initialize ConfigManager
        from Config.AppConfig.config import ConfigManager
        self.config_manager = ConfigManager()

        # Set frame properties
        self.setObjectName("chatFilesProcessingFrame")
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)

        # Apply mobile optimizations if in phone layout
        if self.is_phone_layout:
            MobileOptimizations.apply_optimizations(self)

        # Initialize the UI
        if self.is_phone_layout:
            self._init_phone_ui()
        else:
            self._init_desktop_ui()

        try:
            # Initialize CodeAnalysis instance
            self.code_analysis = CodeAnalysis(parent=self)
            self.code_analysis.analysisStarted.connect(self._on_analysis_started)
            self.code_analysis.analysisFinished.connect(self._on_analysis_finished)
            self.code_analysis.analysisStopped.connect(self._on_analysis_stopped)

            # Add CodeAnalysis UI to the layout (for desktop)
            if not self.is_phone_layout:
                self.layout().addWidget(self.code_analysis)

        except Exception as e:
            logger.error(f"Error initializing CodeAnalysis: {e}")
            self._show_error("Initialization Error", f"Failed to initialize CodeAnalysis: {e}")

        # Connect signals for system prompt and analysis
        self.system_prompt_textedit.textChanged.connect(self._sync_system_prompt)
        self.analysisRequested.connect(self.code_analysis._request_analysis)

        # Final setup
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
        # Set up ChatBubbleDelegate for mobile
        self.chat_history_list.setItemDelegate(ChatBubbleDelegate())
        # Apply mobile styles
        MobileStyles.apply_mobile_theme(self.chat_history_list)
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
        
        # Processing sheet (CodeAnalysis embedded)
        self.processing_sheet = BottomSheet(self)
        processing_content = QWidget()
        processing_layout = QVBoxLayout(processing_content)
        
        # Add CodeAnalysis UI to processing sheet
        processing_layout.addWidget(self.code_analysis)
        
        self.processing_sheet.content.setWidget(processing_content)
        self.processing_sheet.hide()
    
    def _init_desktop_ui(self):
        """Initialize desktop UI."""
        # Main vertical layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Title
        title_label = QLabel("AI Chat Files Processing")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("desktopTitle")
        layout.addWidget(title_label)

        # Input Directory Section
        self._init_input_directory_section(layout)

        # Output Directory Section
        self._init_output_directory_section(layout)

        # Extensions Section
        self._init_extensions_section(layout)

        # System Prompt Section
        self._init_system_prompt_section(layout)

        # Analysis Controls
        self._init_analysis_controls(layout)

        # Progress Section
        self._init_progress_section(layout)

        # Results Section
        self._init_results_section(layout)

        # Add CodeAnalysis UI
        layout.addWidget(self.code_analysis)

        layout.addStretch()

    def _init_input_directory_section(self, layout):
        """Initialize the input directory selection section."""
        input_layout = QHBoxLayout()

        input_dir_label = QLabel("Input Directory:")
        input_dir_label.setObjectName("inputDirLabel")

        self.input_dir_lineedit = QLineEdit()
        self.input_dir_lineedit.setObjectName("inputDirLineEdit")
        self.input_dir_lineedit.setText(self.config_manager.get('input_directory', './input'))

        input_dir_browse = QPushButton("Browse")
        input_dir_browse.setIcon(QIcon(ICONS.get('browse', '')))
        input_dir_browse.setObjectName("inputDirBrowseButton")
        input_dir_browse.clicked.connect(self._browse_input_directory)

        input_layout.addWidget(input_dir_label)
        input_layout.addWidget(self.input_dir_lineedit)
        input_layout.addWidget(input_dir_browse)

        layout.addLayout(input_layout)

    def _init_output_directory_section(self, layout):
        """Initialize the output directory selection section."""
        output_layout = QHBoxLayout()

        output_dir_label = QLabel("Output Directory:")
        output_dir_label.setObjectName("outputDirLabel")

        self.output_dir_lineedit = QLineEdit()
        self.output_dir_lineedit.setObjectName("outputDirLineEdit")
        self.output_dir_lineedit.setText(self.config_manager.get('output_directory', './output'))

        output_dir_browse = QPushButton("Browse")
        output_dir_browse.setIcon(QIcon(ICONS.get('browse', '')))
        output_dir_browse.setObjectName("outputDirBrowseButton")
        output_dir_browse.clicked.connect(self._browse_output_directory)

        output_layout.addWidget(output_dir_label)
        output_layout.addWidget(self.output_dir_lineedit)
        output_layout.addWidget(output_dir_browse)

        layout.addLayout(output_layout)

    def _init_extensions_section(self, layout):
        """Initialize the file extensions section."""
        extensions_layout = QHBoxLayout()

        extensions_label = QLabel("Extensions (comma-separated):")
        extensions_label.setObjectName("extensionsLabel")

        self.extensions_lineedit = QLineEdit()
        self.extensions_lineedit.setObjectName("extensionsLineEdit")
        self.extensions_lineedit.setPlaceholderText("py,js,cpp")
        self.extensions_lineedit.setText(self.config_manager.get('file_extensions', 'py,js,cpp'))

        extensions_layout.addWidget(extensions_label)
        extensions_layout.addWidget(self.extensions_lineedit)

        layout.addLayout(extensions_layout)

    def _init_system_prompt_section(self, layout):
        """Initialize the system prompt section with proper theming."""
        system_prompt_label = QLabel("System Prompt:")
        system_prompt_label.setObjectName("systemPromptAnalysisLabel")  # Add theming
        apply_mobile_style(system_prompt_label, "mobileSubheader")
        layout.addWidget(system_prompt_label)

        # Initialize the system prompt text edit with proper styling
        self.system_prompt_textedit = QTextEdit()
        self.system_prompt_textedit.setObjectName("systemPromptAnalysisTextEdit")  # Add theming
        self.system_prompt_textedit.setMinimumHeight(100)
        self.system_prompt_textedit.textChanged.connect(self._sync_system_prompt)
        self.system_prompt_textedit.setText(self.config_manager.get('system_prompt', 'Analyze the provided code files.'))

        # Apply styles directly
        self.system_prompt_textedit.setStyleSheet("""
            QTextEdit#systemPromptAnalysisTextEdit {
                background-color: var(--background-color);
                color: var(--text-color);
                border: 1px solid var(--border-color);
                border-radius: 4px;
                padding: 8px;
            }
        """)

        layout.addWidget(self.system_prompt_textedit)

    def _init_analysis_controls(self, layout):
        """Initialize the analysis control buttons."""
        controls_layout = QHBoxLayout()

        self.start_analysis_button = QPushButton("Start Analysis")
        self.start_analysis_button.setIcon(QIcon(ICONS.get('start', '')))
        self.start_analysis_button.setObjectName("startAnalysisButton")
        self.start_analysis_button.clicked.connect(self._request_analysis)

        self.stop_analysis_button = QPushButton("Stop Analysis")
        self.stop_analysis_button.setIcon(QIcon(ICONS.get('stop', '')))
        self.stop_analysis_button.setEnabled(False)
        self.stop_analysis_button.setObjectName("stopAnalysisButton")
        self.stop_analysis_button.clicked.connect(self._stop_analysis)

        controls_layout.addWidget(self.start_analysis_button)
        controls_layout.addWidget(self.stop_analysis_button)

        layout.addLayout(controls_layout)

    def _init_progress_section(self, layout):
        """Initialize the progress tracking section."""
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setObjectName("analysisProgressBar")
        layout.addWidget(self.progress_bar)

    def _init_results_section(self, layout):
        """Initialize the analysis results section."""
        self.results_textedit = QTextEdit()
        self.results_textedit.setReadOnly(True)
        self.results_textedit.setVisible(False)
        self.results_textedit.setObjectName("analysisResultsTextEdit")
        layout.addWidget(self.results_textedit)

    def _setup_connections(self) -> None:
        """Connect all signals to their respective slots."""
        if self.is_phone_layout:
            # Chat management
            self.new_chat_button.clicked.connect(self._handle_new_chat)
            self.upload_button.clicked.connect(self._handle_upload_file)
            self.more_options_button.clicked.connect(self._show_chat_options_sheet)
            self.chat_history_list.itemClicked.connect(self._handle_chat_selected)

            # Processing controls are handled via CodeAnalysis
        else:
            # Desktop Chat management
            self.new_chat_button.clicked.connect(self._handle_new_chat)
            self.upload_button.clicked.connect(self._handle_upload_file)
            self.more_options_button.clicked.connect(self._show_chat_options_sheet)
            self.chat_history_list.itemClicked.connect(self._handle_chat_selected)

            # Desktop Processing is handled via CodeAnalysis
            # The CodeAnalysis instance is already embedded and connected
            pass

    def _init_processing_controls(self, layout):
        """Initialize processing controls for mobile interface."""
        # This method is deprecated as processing is handled via CodeAnalysis embedded
        pass

    def _browse_input_directory(self):
        """Open a dialog to select the input directory."""
        try:
            # Open a directory selection dialog
            directory = QFileDialog.getExistingDirectory(
                self, 
                "Select Input Directory",
                self.input_dir_lineedit.text()
            )
            if directory:
                if self.is_phone_layout:
                    self.processing_sheet.input_dir_button.setText(directory)
                else:
                    self.input_dir_lineedit.setText(directory)
                self.config_manager.set('input_directory', directory)
                logger.debug(f"Input directory selected: {directory}")
        except Exception as e:
            logger.error(f"Error browsing input directory: {e}")
            self._show_error("Directory Selection Error", str(e))

    def _browse_output_directory(self):
        """Open a dialog to select the output directory."""
        try:
            # Open a directory selection dialog
            directory = QFileDialog.getExistingDirectory(
                self, 
                "Select Output Directory",
                self.output_dir_lineedit.text()
            )
            if directory:
                if self.is_phone_layout:
                    self.processing_sheet.output_dir_button.setText(directory)
                else:
                    self.output_dir_lineedit.setText(directory)
                self.config_manager.set('output_directory', directory)
                logger.debug(f"Output directory selected: {directory}")
        except Exception as e:
            logger.error(f"Error browsing output directory: {e}")
            self._show_error("Directory Selection Error", str(e))

    def _handle_start_processing(self) -> None:
        """Start the processing operation (desktop)."""
        # This method is deprecated as processing is handled via CodeAnalysis embedded
        pass

    def _request_analysis(self):
        """Request analysis by emitting the signal."""
        params = self._get_analysis_parameters()
        if not params:
            QMessageBox.warning(self, "Input Error", "Please provide all required parameters.")
            return
        self.analysisRequested.emit(params)
        self.start_analysis_button.setEnabled(False)
        self.stop_analysis_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.results_textedit.setVisible(True)
        self.results_textedit.append("Analysis started...")

    def _stop_analysis(self) -> None:
        """Stop the ongoing processing."""
        self.code_analysis._stop_analysis()
        self.stop_analysis_button.setEnabled(False)

    def _on_analysis_started(self, params: dict):
        """Handle when analysis starts."""
        logger.info(f"Analysis started with parameters: {params}")

    def _on_analysis_finished(self):
        """Handle when analysis finishes."""
        self.start_analysis_button.setEnabled(True)
        self.stop_analysis_button.setEnabled(False)
        self.progress_bar.setValue(100)
        self.results_textedit.append("Analysis completed!")
        logger.info("Analysis completed.")
        self.processingFinished.emit()

    def _on_analysis_stopped(self):
        """Handle when analysis is stopped."""
        self.start_analysis_button.setEnabled(True)
        self.stop_analysis_button.setEnabled(False)
        self.results_textedit.append("Analysis stopped.")
        logger.info("Analysis stopped.")
        self.processingFinished.emit()

    def _get_analysis_parameters(self) -> Optional[Dict]:
        """Prepare parameters for analysis from config."""
        input_dir = self.config_manager.get('input_directory', './input')
        output_dir = self.config_manager.get('output_directory', './output')
        system_prompt = self.system_prompt_textedit.toPlainText()
        file_extensions = self.extensions_lineedit.text()

        if not all([input_dir, output_dir, system_prompt]):
            QMessageBox.warning(self, "Input Error", "Please provide input/output directories and system prompt.")
            return None

        # Optionally, validate directories and file extensions here

        return {
            "input_dir": input_dir,
            "output_dir": output_dir,
            "system_prompt": system_prompt,
            "file_extensions": file_extensions.split(',') if file_extensions else []
        }

    def _show_chat_options_sheet(self):
        """Show the chat options bottom sheet."""
        self.chat_options_sheet.show()
        animation = QPropertyAnimation(self.chat_options_sheet, b"geometry")
        animation.setDuration(300)
        animation.setStartValue(
            QRect(0, self.height(), self.width(), self.height() * 0.7)
        )
        animation.setEndValue(
            QRect(0, self.height() * 0.3, self.width(), self.height() * 0.7)
        )
        animation.start()

    def _handle_new_chat(self) -> None:
        """Handle creating a new chat."""
        try:
            chat_id = start_new_chat({}, self.chat_history_list, None)
            self.chatStarted.emit(chat_id)
            self.save_state()
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
                self.save_state()
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

    def _sync_system_prompt(self):
        """Handle synchronization of the system prompt."""
        try:
            prompt_content = self.system_prompt_textedit.toPlainText()
            save_system_prompt(prompt_content)
            self.config_manager.set('system_prompt', prompt_content)
            logger.debug("System prompt synced successfully in AIChatFilesProcessing.")
        except Exception as e:
            logger.error(f"Error syncing system prompt in AIChatFilesProcessing: {e}")
            self._show_error("Sync Error", f"Failed to sync system prompt: {e}")

    def _show_error(self, title: str, message: str) -> None:
        """Show error message to user."""
        QMessageBox.critical(self, title, message)

    def save_state(self) -> None:
        """Save current state to configuration."""
        try:
            state = {
                'input_directory': self.input_dir_lineedit.text(),
                'output_directory': self.output_dir_lineedit.text(),
                'file_extensions': self.extensions_lineedit.text(),
                'system_prompt': self.system_prompt_textedit.toPlainText(),
                'selected_chat': self.get_selected_chat_id(),
                'progress_visible': self.progress_bar.isVisible(),
                'progress_value': self.progress_bar.value(),
                'results_visible': self.results_textedit.isVisible(),
                'results_content': self.results_textedit.toPlainText()
            }
            self.config_manager.save_left_menu_state(state)
            self.stateChanged.emit(state)
            
        except Exception as e:
            logger.error(f"Error saving state: {str(e)}")
            self._show_error("Save Error", f"Failed to save state: {str(e)}")

    def load_state(self) -> None:
        """Load saved state from configuration."""
        try:
            state = self.config_manager.load_left_menu_state()
            if state:
                self.input_dir_lineedit.setText(state.get('input_directory', './input'))
                self.output_dir_lineedit.setText(state.get('output_directory', './output'))
                self.extensions_lineedit.setText(state.get('file_extensions', 'py,js,cpp'))
                self.system_prompt_textedit.setText(state.get('system_prompt', 'Analyze the provided code files.'))
                selected_chat = state.get('selected_chat', None)
                if selected_chat:
                    self.select_chat(selected_chat)
                self.progress_bar.setVisible(state.get('progress_visible', False))
                self.progress_bar.setValue(state.get('progress_value', 0))
                self.results_textedit.setVisible(state.get('results_visible', False))
                self.results_textedit.setText(state.get('results_content', ''))
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
            self.results_textedit.clear()
            self.results_textedit.setVisible(False)
            self.start_analysis_button.setEnabled(True)
            self.stop_analysis_button.setEnabled(False)
            self.input_dir_lineedit.clear()
            self.output_dir_lineedit.clear()
            self.system_prompt_textedit.clear()
            self.extensions_lineedit.clear()
        except Exception as e:
            logger.error(f"Error resetting processing: {str(e)}")
            self._show_error("Reset Error", f"Failed to reset processing: {str(e)}")

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
        return (self.code_analysis.is_processing())

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
