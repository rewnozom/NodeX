# ./frontend/pages/qframes/chat/code_analysis.py

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QRect, QEasingCurve, QEvent, QThread
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QScrollArea,
    QPushButton, QLabel, QLineEdit, QTextEdit,
    QFileDialog, QMessageBox, QProgressBar, QWidget, QSwipeGesture
)

from log.logger import logger
from Config.AppConfig.icon_config import ICONS
from ai_agent.config.prompt_manager import (
    load_specific_system_prompt, save_system_prompt
)
from ..helper.workers import ProcessingWorker

from Config.phone_config.phone_functions import (
    MobileStyles, MobileOptimizations, MobileBottomSheet,
    apply_mobile_style
)
from frontend._layout.layout_manager import LayoutManager  # Om behövligt

class AnalysisBottomSheet(MobileBottomSheet):
    """Mobile-friendly bottom sheet for analysis settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        """Setup the bottom sheet UI."""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 10, 0, 0)

        # Handle bar
        handle = QFrame()
        handle.setObjectName("sheetHandle")
        handle.setFixedSize(40, 4)
        handle_layout = QHBoxLayout()
        handle_layout.addWidget(handle)
        handle_layout.setAlignment(Qt.AlignCenter)
        self.layout.addLayout(handle_layout)

        # Title
        title = QLabel("Analysis Settings")
        title.setObjectName("sheetTitle")
        title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("sheetScroll")
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        scroll.setWidget(self.content)
        self.layout.addWidget(scroll)

        # Directory selection
        self.input_dir_button = QPushButton("Select Input Directory")
        self.input_dir_button.setMinimumHeight(50)
        self.input_dir_button.clicked.connect(lambda: self.parent._browse_input_directory())
        
        self.output_dir_button = QPushButton("Select Output Directory")
        self.output_dir_button.setMinimumHeight(50)
        self.output_dir_button.clicked.connect(lambda: self.parent._browse_output_directory())

        # Extensions input
        self.extensions_input = QLineEdit()
        self.extensions_input.setPlaceholderText("File extensions (e.g., py,js,cpp)")
        self.extensions_input.setMinimumHeight(50)

        # System prompt
        self.system_prompt_edit = QTextEdit()
        self.system_prompt_edit.setPlaceholderText("Enter system prompt...")
        self.system_prompt_edit.setMaximumHeight(150)

        # Add widgets to sheet
        for widget in [
            self.input_dir_button,
            self.output_dir_button,
            self.extensions_input,
            QLabel("System Prompt:"),
            self.system_prompt_edit
        ]:
            self.content_layout.addWidget(widget)

        self.setStyleSheet("""
            QWidget#analysisBottomSheet {
                background: white;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }
            QFrame#sheetHandle {
                background: #E0E0E0;
                border-radius: 2px;
            }
            QLabel#sheetTitle {
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton {
                margin: 5px 0;
                padding: 10px;
                border: 1px solid #E0E0E0;
                border-radius: 10px;
                background-color: #F5F5F5;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 10px;
                padding: 10px;
                background-color: #FFFFFF;
            }
        """)

class CodeAnalysis(QFrame):
    """
    A QFrame that handles code analysis functionality.
    Provides interface for analyzing code files with specified parameters.
    """

    # Define signals
    analysisStarted = Signal(dict)    # Emitted when analysis starts with parameters
    analysisFinished = Signal()       # Emitted when analysis completes
    analysisStopped = Signal()        # Emitted when analysis is stopped
    themeChanged = Signal(str)        # Emitted when theme changes

    def __init__(self, parent=None):
        """Initialize the code analysis frame."""
        super().__init__(parent)
        self.parent = parent
        self.worker = None
        self.thread = None
        self.is_phone_layout = self.parent.config.get('enable_phone_layout', False)

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
        self.settings_button = QPushButton()
        self.settings_button.setIcon(QIcon(ICONS.get('settings', '')))
        self.settings_button.setToolTip("Analysis Settings")
        self.settings_button.setMinimumSize(50, 50)
        self.settings_button.clicked.connect(lambda: self.show_bottom_sheet("settings"))

        self.start_button = QPushButton()
        self.start_button.setIcon(QIcon(ICONS.get('play', '')))
        self.start_button.setToolTip("Start Analysis")
        self.start_button.setMinimumSize(50, 50)
        self.start_button.clicked.connect(self._start_analysis)

        for btn in [self.settings_button, self.start_button]:
            btn.setObjectName("mobileActionButton")
            apply_mobile_style(btn, "mobileActionButton")
            status_layout.addWidget(btn)

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

        # Initialize bottom sheets
        self.settings_sheet = AnalysisBottomSheet(self)
        self.settings_sheet.hide()

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

        layout.addStretch()

    def _init_input_directory_section(self, layout):
        """Initialize the input directory selection section."""
        input_layout = QHBoxLayout()

        input_dir_label = QLabel("Input Directory:")
        input_dir_label.setObjectName("inputDirLabel")

        self.input_dir_lineedit = QLineEdit()
        self.input_dir_lineedit.setObjectName("inputDirLineEdit")

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

        extensions_layout.addWidget(extensions_label)
        extensions_layout.addWidget(self.extensions_lineedit)

        layout.addLayout(extensions_layout)

    def _init_system_prompt_section(self, layout):
        """Initialize the system prompt section with proper theming."""
        system_prompt_label = QLabel("System Prompt:")
        system_prompt_label.setObjectName("systemPromptAnalysisLabel")  # Add theming
        layout.addWidget(system_prompt_label)

        # Initialize the system prompt text edit with proper styling
        self.system_prompt_textedit = QTextEdit()
        self.system_prompt_textedit.setObjectName("systemPromptAnalysisTextEdit")  # Add theming
        self.system_prompt_textedit.setMinimumHeight(100)
        self.system_prompt_textedit.textChanged.connect(self._sync_system_prompt)

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

        self.stop_analysis_button = QPushButton("Stop Analysis")
        self.stop_analysis_button.setIcon(QIcon(ICONS.get('stop', '')))
        self.stop_analysis_button.setEnabled(False)
        self.stop_analysis_button.setObjectName("stopAnalysisButton")

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
        """Connect all signals to their slots."""
        self.start_analysis_button.clicked.connect(self._start_analysis)
        self.stop_analysis_button.clicked.connect(self._stop_analysis)

    def show_bottom_sheet(self, sheet_name: str):
        """Show the specified bottom sheet with animation."""
        sheet = getattr(self, f"{sheet_name}_sheet")
        if sheet and sheet.isHidden():
            sheet.show()
            self._animate_sheet(sheet, True)

    def hide_bottom_sheet(self, sheet_name: str):
        """Hide the specified bottom sheet with animation."""
        sheet = getattr(self, f"{sheet_name}_sheet")
        if sheet and not sheet.isHidden():
            self._animate_sheet(sheet, False)

    def _animate_sheet(self, sheet: QWidget, show: bool):
        """Animate bottom sheet showing/hiding."""
        animation = QPropertyAnimation(sheet, b"geometry")
        animation.setDuration(300)
        animation.setEasingCurve(QEasingCurve.OutCubic)

        if show:
            start_rect = QRect(0, self.height(), self.width(), self.height() * 0.8)
            end_rect = QRect(0, self.height() * 0.2, self.width(), self.height() * 0.8)
        else:
            start_rect = sheet.geometry()
            end_rect = QRect(0, self.height(), self.width(), self.height() * 0.8)

        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)

        if not show:
            animation.finished.connect(sheet.hide)

        animation.start()

    def _browse_input_directory(self):
        """Open dialog to browse for input directory."""
        try:
            directory = QFileDialog.getExistingDirectory(
                self, "Select Input Directory",
                self.input_dir_lineedit.text() if hasattr(self, 'input_dir_lineedit') else ''
            )
            if directory:
                if self.is_phone_layout:
                    if hasattr(self, 'settings_sheet'):
                        self.settings_sheet.input_dir_button.setText(directory)
                else:
                    self.input_dir_lineedit.setText(directory)
                logger.debug(f"Input directory selected: {directory}")
        except Exception as e:
            logger.error(f"Error browsing input directory: {str(e)}")
            self._show_error("Directory Selection Error", str(e))

    def _browse_output_directory(self):
        """Open dialog to browse for output directory."""
        try:
            directory = QFileDialog.getExistingDirectory(
                self, "Select Output Directory",
                self.output_dir_lineedit.text() if hasattr(self, 'output_dir_lineedit') else ''
            )
            if directory:
                if self.is_phone_layout:
                    if hasattr(self, 'settings_sheet'):
                        self.settings_sheet.output_dir_button.setText(directory)
                else:
                    self.output_dir_lineedit.setText(directory)
                logger.debug(f"Output directory selected: {directory}")
        except Exception as e:
            logger.error(f"Error browsing output directory: {str(e)}")
            self._show_error("Directory Selection Error", str(e))

    def _sync_system_prompt(self):
        """Sync the system prompt with backend and update UI."""
        try:
            prompt_content = self.system_prompt_textedit.toPlainText()
            save_system_prompt(prompt_content)
            self.agent_system_prompt_content = prompt_content
        except Exception as e:
            logger.error(f"Error saving system prompt: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save system prompt: {str(e)}")

    def _start_analysis(self):
        """Start the code analysis process."""
        params = self.get_analysis_parameters()

        if not all([params['input_dir'], params['output_dir']]):
            QMessageBox.warning(self, "Input Error",
                                "Please specify both input and output directories.")
            return

        # Update UI state
        self._update_ui_analysis_started()

        # Create worker using our centralized ProcessingWorker
        try:
            self.worker = ProcessingWorker(
                input_dir=params['input_dir'],
                output_dir=params['output_dir'],
                system_prompt=params['system_prompt'],
                llm=self.parent.llm if self.parent else None,
                worker_type="code_analysis"
            )

            # Connect worker signals
            self.worker.progress_update.connect(self.update_progress)
            self.worker.processing_finished.connect(self._analysis_finished)
            self.worker.signals.error.connect(self._handle_analysis_error)
            self.worker.signals.status_changed.connect(self._update_status)

            # Start the worker
            self.thread = QThread()
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.thread.start()

            self.analysisStarted.emit(params)

        except Exception as e:
            self._handle_analysis_error(str(e))

    def _stop_analysis(self):
        """Stop the ongoing analysis."""
        if self.worker:
            self.worker.stop()
            self.stop_analysis_button.setEnabled(False)
            self.results_textedit.append("Stopping analysis...")
            self.analysisStopped.emit()
        else:
            QMessageBox.warning(self, "No Analysis Task",
                                "There is no analysis task to stop.")

    def _update_ui_analysis_started(self):
        """Update UI state when analysis starts."""
        self.start_analysis_button.setEnabled(False)
        self.stop_analysis_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.results_textedit.setVisible(True)
        self.results_textedit.clear()
        self.progress_bar.setValue(0)

    def _handle_analysis_error(self, error_msg: str):
        """Handle analysis errors with proper UI updates."""
        logger.error(f"Analysis error: {error_msg}")
        self.results_textedit.append(f"Error: {error_msg}")
        self.start_analysis_button.setEnabled(True)
        self.stop_analysis_button.setEnabled(False)
        QMessageBox.critical(self, "Analysis Error", str(error_msg))

    def _update_status(self, status: str):
        """Update status in results text edit."""
        self.results_textedit.append(f"Status: {status}")

    def update_progress(self, item_name: str, status: str):
        """Update the progress display."""
        self.results_textedit.append(f"{item_name}: {status}")

        if status == "Completed":
            self.progress_bar.setValue(100)
            self._analysis_finished()
        else:
            # Increment progress bar
            current_value = self.progress_bar.value()
            if current_value < 95:  # Leave room for completion
                self.progress_bar.setValue(current_value + 5)

    def _analysis_finished(self):
        """Handle analysis completion."""
        self.start_analysis_button.setEnabled(True)
        self.stop_analysis_button.setEnabled(False)
        self.results_textedit.append("\nAnalysis completed!")
        self.analysisFinished.emit()

    def get_analysis_parameters(self) -> dict:
        """Get current analysis parameters including system prompt."""
        return {
            'input_dir': self.input_dir_lineedit.text(),
            'output_dir': self.output_dir_lineedit.text(),
            'extensions': self.extensions_lineedit.text(),
            'system_prompt': self.system_prompt_textedit.toPlainText()
        }

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

    def save_state(self) -> None:
        """Save current state to configuration."""
        try:
            state = {
                'input_dir': self.input_dir_lineedit.text(),
                'output_dir': self.output_dir_lineedit.text(),
                'extensions': self.extensions_lineedit.text(),
                'system_prompt': self.system_prompt_textedit.toPlainText(),
                'results': self.results_textedit.toPlainText(),
                'progress': self.progress_bar.value(),
                'progress_visible': self.progress_bar.isVisible(),
                'results_visible': self.results_textedit.isVisible()
            }
            self.parent.config.save_code_analysis_state(state)
            self.analysisStarted.emit(state)
        except Exception as e:
            logger.error(f"Error saving state: {str(e)}")
            QMessageBox.critical(self, "Save Error", f"Failed to save state: {str(e)}")

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

