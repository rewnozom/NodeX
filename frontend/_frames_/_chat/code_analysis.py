# ./frontend/pages/qframes/chat/code_analysis.py

from PySide6.QtCore import Qt, Signal, QThread, QEvent
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QScrollArea,
    QPushButton, QLabel, QLineEdit, QTextEdit,
    QFileDialog, QMessageBox, QProgressBar, QWidget, QSwipeGesture
)
from typing import List, Optional, Union, Dict
from log.logger import logger
from Config.AppConfig.icon_config import ICONS
from ai_agent.config.prompt_manager import (
    load_specific_system_prompt, save_system_prompt
)
from .._helper.workers import ProcessingWorker

from Config.phone_config.phone_functions import (
    MobileStyles, MobileOptimizations, MobileBottomSheet,
    apply_mobile_style
)
from frontend._layout.layout_manager import LayoutManager  # Om behövligt

class CodeAnalysis(QFrame):
    """
    A QFrame that handles code analysis functionality.
    Provides interface for analyzing code files with specified parameters.
    """

    # Define signals
    analysisStarted = Signal(dict)
    analysisFinished = Signal()
    analysisStopped = Signal()
    themeChanged = Signal(str)

    def __init__(self, parent=None):
        """Initialize the code analysis frame."""
        super().__init__(parent)
        self.parent = parent
        self.worker = None
        self.thread = None
        self.is_phone_layout = self.parent.config_manager.get('enable_phone_layout', False)

        # Initialize ConfigManager
        from Config.AppConfig.config import ConfigManager
        self.config_manager = ConfigManager()

        # Set frame properties
        self.setObjectName("codeAnalysisFrame")
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)

        # Apply mobile optimizations if in phone layout
        if self.is_phone_layout:
            MobileOptimizations.apply_optimizations(self)

        # Initialize UI based on layout type
        if self.is_phone_layout:
            self._init_phone_ui()
        else:
            self._init_desktop_ui()

        self._connect_signals()
        self.load_state()  # Load any saved state

    def _init_phone_ui(self):
        """Initialize mobile-optimized UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Status and Action Buttons
        status_layout = QHBoxLayout()

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("mobileStatusLabel")
        status_layout.addWidget(self.status_label)

        # Action buttons
        self.start_button = QPushButton()
        self.start_button.setIcon(QIcon(ICONS.get('play', '')))
        self.start_button.setToolTip("Start Analysis")
        self.start_button.setMinimumSize(50, 50)
        self.start_button.clicked.connect(self._start_analysis)
        self.start_button.setObjectName("mobileActionButton")
        apply_mobile_style(self.start_button, "mobileActionButton")
        status_layout.addWidget(self.start_button)

        self.stop_button = QPushButton()
        self.stop_button.setIcon(QIcon(ICONS.get('stop', '')))
        self.stop_button.setToolTip("Stop Analysis")
        self.stop_button.setMinimumSize(50, 50)
        self.stop_button.setEnabled(False)
        self.stop_button.setObjectName("mobileActionButton")
        apply_mobile_style(self.stop_button, "mobileActionButton")
        self.stop_button.clicked.connect(self._stop_analysis)
        status_layout.addWidget(self.stop_button)

        layout.addLayout(status_layout)

        # Results area
        self.results_view = QTextEdit()
        self.results_view.setReadOnly(True)
        self.results_view.setObjectName("mobileResultsView")
        self.results_view.setPlaceholderText("Analysis results will appear here...")
        apply_mobile_style(self.results_view, "mobileResultsView")
        layout.addWidget(self.results_view)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setObjectName("mobileProgressBar")
        apply_mobile_style(self.progress_bar, "mobileProgressBar")
        layout.addWidget(self.progress_bar)

        # Apply overall mobile styling
        self.setStyleSheet("""
            QLabel#mobileStatusLabel {
                font-size: 16px;
                color: #555555;
            }
            QTextEdit#mobileResultsView {
                border: 1px solid #E0E0E0;
                border-radius: 10px;
                padding: 10px;
                background-color: #F9F9F9;
                font-size: 14px;
            }
            QProgressBar#mobileProgressBar {
                border: none;
                border-radius: 10px;
                height: 10px;
                background-color: #F0F0F0;
            }
            QProgressBar#mobileProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 10px;
            }
        """)

    def _init_desktop_ui(self):
        """Initialize desktop UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Title
        title_label = QLabel("Code Analysis")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("codeAnalysisTitle")
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

        # Add Stretch
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
        self.extensions_lineedit.setText(','.join(self.config_manager.get('file_extensions', ['py', 'js', 'cpp'])))

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
        self.stop_analysis_button.setObjectName("stopAnalysisButton")
        self.stop_analysis_button.setEnabled(False)
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

    def _connect_signals(self):
        """Connect all signals to their respective slots."""
        pass  # Signals are connected in AIChatFilesProcessing via CodeAnalysis

    def _browse_input_directory(self):
        """Open dialog to browse for input directory."""
        try:
            directory = QFileDialog.getExistingDirectory(
                self, "Select Input Directory",
                self.input_dir_lineedit.text()
            )
            if directory:
                self.input_dir_lineedit.setText(directory)
                self.config_manager.set('input_directory', directory)
                logger.debug(f"Input directory selected: {directory}")
        except Exception as e:
            logger.error(f"Error browsing input directory: {str(e)}")
            self._show_error("Directory Selection Error", str(e))

    def _browse_output_directory(self):
        """Open dialog to browse for output directory."""
        try:
            directory = QFileDialog.getExistingDirectory(
                self, "Select Output Directory",
                self.output_dir_lineedit.text()
            )
            if directory:
                self.output_dir_lineedit.setText(directory)
                self.config_manager.set('output_directory', directory)
                logger.debug(f"Output directory selected: {directory}")
        except Exception as e:
            logger.error(f"Error browsing output directory: {str(e)}")
            self._show_error("Directory Selection Error", str(e))

    def _sync_system_prompt(self):
        """Handle synchronization of the system prompt."""
        try:
            prompt_content = self.parent.system_prompt_textedit.toPlainText()
            save_system_prompt(prompt_content)
            self.config_manager.set('system_prompt', prompt_content)
            logger.debug("System prompt synced successfully in CodeAnalysis.")
        except Exception as e:
            logger.error(f"Error syncing system prompt in CodeAnalysis: {e}")
            self._show_error("Sync Error", f"Failed to sync system prompt: {e}")

    def _show_error(self, title: str, message: str) -> None:
        """Show error message to user."""
        QMessageBox.critical(self, title, message)

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
        self.analysisStopped.emit()
        self.stop_analysis_button.setEnabled(False)
        self.results_textedit.append("Analysis stopped.")
        if self.worker:
            self.worker.stop()

    def _on_analysis_started(self, params: dict):
        """Handle when analysis starts."""
        logger.info(f"Analysis started with parameters: {params}")
        self.analysisStarted.emit(params)

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
        self.processingStopped.emit()

    def _get_analysis_parameters(self) -> Optional[Dict]:
        """Prepare parameters for analysis from config."""
        input_dir = self.config_manager.get('input_directory', './input')
        output_dir = self.config_manager.get('output_directory', './output')
        system_prompt = self.system_prompt_textedit.toPlainText()
        file_extensions = self.extensions_lineedit.text()

        if not all([input_dir, output_dir, system_prompt]):
            QMessageBox.warning(self, "Input Error", "Please provide input/output directories and system prompt.")
            return None

        # Process file extensions
        extensions = [ext.strip() for ext in file_extensions.split(',') if ext.strip()]
        if not extensions:
            QMessageBox.warning(self, "Input Error", "Please provide at least one file extension.")
            return None

        return {
            "input_dir": input_dir,
            "output_dir": output_dir,
            "system_prompt": system_prompt,
            "file_extensions": extensions
        }

    def _show_error(self, title: str, message: str) -> None:
        """Show error message to user."""
        logger.error(f"{title}: {message}")
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
            state = self.parent.config.load_code_analysis_state()
            if state:
                self.input_dir_lineedit.setText(state.get('input_dir', ''))
                self.output_dir_lineedit.setText(state.get('output_dir', ''))
                self.extensions_lineedit.setText(state.get('extensions', ''))
                self.system_prompt_textedit.setPlainText(state.get('system_prompt', ''))
                self.results_textedit.setText(state.get('results', ''))
                self.progress_bar.setValue(state.get('progress', 0))
                self.progress_bar.setVisible(state.get('progress_visible', False))
                self.results_textedit.setVisible(state.get('results_visible', False))
        except Exception as e:
            logger.error(f"Error loading state: {str(e)}")
            QMessageBox.critical(self, "Load Error", f"Failed to load state: {str(e)}")



    def _show_error(self, title: str, message: str) -> None:
        """Show error message to user."""
        logger.error(f"{title}: {message}")
        QMessageBox.critical(self, title, message)

    def clear_results(self):
        """Clear analysis results and reset UI state."""
        self.results_textedit.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.results_textedit.setVisible(False)

    def update_theme(self, theme_name: str):
        """Update the theme of the frame and all child widgets."""
        # Update frame theme
        self.setObjectName(f"codeAnalysisFrame_{theme_name}")

        # Update system prompt text edit theme
        self.system_prompt_textedit.setObjectName(f"systemPromptAnalysisTextEdit_{theme_name}")

        # Update all child widgets' themes
        for widget in self.findChildren(QWidget):
            if widget.objectName():
                widget.setObjectName(f"{widget.objectName()}_{theme_name}")

        # Force style update
        self.style().unpolish(self)
        self.style().polish(self)

        # Emit theme changed signal
        self.themeChanged.emit(theme_name)

    def load_specific_system_prompt(self, prompt_name: str):
        """Load a specific system prompt and apply proper formatting."""
        try:
            prompt_content = load_specific_system_prompt(prompt_name)
            if prompt_content:
                self.system_prompt_textedit.setPlainText(prompt_content)
                # Store the content in the class variable
                self.agent_system_prompt_content = prompt_content
        except Exception as e:
            logger.error(f"Error loading system prompt: {str(e)}")

    def handle_parent_close(self) -> None:
        """Handle cleanup when parent is closing."""
        if self.is_processing():
            self._handle_stop_analysis()
        self.save_state()

    def is_processing(self) -> bool:
        """Check if processing is currently active."""
        return (self.worker is not None and 
                hasattr(self.worker, '_is_running') and 
                self.worker._is_running)

    # (Valfritt) Implementera svepgester för att hantera bottenarket
    def eventFilter(self, source, event):
        if event.type() == QEvent.Gesture:
            return self._handle_gesture_event(event)
        return super().eventFilter(source, event)

    def _handle_gesture_event(self, event):
        gesture = event.gesture(Qt.SwipeGesture)
        if gesture:
            if gesture.horizontalDirection() == QSwipeGesture.Left:
                # Handle left swipe if needed
                pass
            elif gesture.horizontalDirection() == QSwipeGesture.Right:
                # Handle right swipe if needed
                pass
            elif gesture.verticalDirection() == QSwipeGesture.Up:
                self.show_bottom_sheet("settings")
            elif gesture.verticalDirection() == QSwipeGesture.Down:
                self.hide_bottom_sheet("settings")
        return True







