# ./frontend/pages/qframes/chat/code_analysis.py



from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QTextEdit, QFileDialog, QMessageBox,
    QProgressBar, QWidget
)

from log.logger import logger
from Config.AppConfig.icon_config import ICONS
from ai_agent.config.prompt_manager import (
    load_specific_system_prompt, save_system_prompt
)
from ..helper.workers import ProcessingWorker

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
        
        # Set frame properties
        self.setObjectName("codeAnalysisFrame")
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        """Initialize the UI components."""
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

    def _browse_input_directory(self):
        """Open dialog to browse for input directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Input Directory",
            self.input_dir_lineedit.text()
        )
        if directory:
            self.input_dir_lineedit.setText(directory)

    def _browse_output_directory(self):
        """Open dialog to browse for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory",
            self.output_dir_lineedit.text()
        )
        if directory:
            self.output_dir_lineedit.setText(directory)

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
            self.worker.run()
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

    def load_system_prompt(self, prompt_name: str):
        """Load a specific system prompt and apply proper formatting."""
        try:
            prompt_content = load_specific_system_prompt(prompt_name)
            if prompt_content:
                self.system_prompt_textedit.setPlainText(prompt_content)
                # Store the content in the class variable
                self.agent_system_prompt_content = prompt_content
        except Exception as e:
            logger.error(f"Error loading system prompt: {str(e)}")

    def get_analysis_parameters(self) -> dict:
        """Get current analysis parameters including system prompt."""
        return {
            'input_dir': self.input_dir_lineedit.text(),
            'output_dir': self.output_dir_lineedit.text(),
            'extensions': self.extensions_lineedit.text(),
            'system_prompt': self.system_prompt_textedit.toPlainText()
        }

    def clear_results(self):
        """Clear analysis results and reset UI state."""
        self.results_textedit.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.results_textedit.setVisible(False)