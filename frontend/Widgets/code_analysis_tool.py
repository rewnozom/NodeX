from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QHBoxLayout, QMessageBox, QFileDialog
from PySide6.QtGui import QIcon
from ai_agent.chat_manager.chat_manager import process_files
from frontend._frames_._helper.workers import FileProcessingWorker, WorkerSignals
from ai_agent.threads.worker_thread import Worker
from log.logger import logger

class CodeAnalysisTool(QWidget):
    def __init__(self, parent=None, icons=None):
        super().__init__(parent)
        self.icons = icons
        self.worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Input Directory
        input_dir_label = QLabel("Input Directory:")
        input_dir_label.setObjectName("inputDirLabel")  # For theming
        self.input_dir_lineedit = QLineEdit()
        self.input_dir_lineedit.setObjectName("inputDirLineEdit")  # For theming
        input_dir_browse_button = QPushButton("Browse")
        input_dir_browse_button.setIcon(QIcon(self.icons.get('browse', '')))  # Ensure 'browse' icon exists
        input_dir_browse_button.setObjectName("inputDirBrowseButton")  # For theming
        input_dir_layout = QHBoxLayout()
        input_dir_layout.addWidget(input_dir_label)
        input_dir_layout.addWidget(self.input_dir_lineedit)
        input_dir_layout.addWidget(input_dir_browse_button)
        layout.addLayout(input_dir_layout)

        # Output Directory
        output_dir_label = QLabel("Output Directory:")
        output_dir_label.setObjectName("outputDirLabel")  # For theming
        self.output_dir_lineedit = QLineEdit()
        self.output_dir_lineedit.setObjectName("outputDirLineEdit")  # For theming
        output_dir_browse_button = QPushButton("Browse")
        output_dir_browse_button.setIcon(QIcon(self.icons.get('browse', '')))  # Reuse 'browse' icon
        output_dir_browse_button.setObjectName("outputDirBrowseButton")  # For theming
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(output_dir_label)
        output_dir_layout.addWidget(self.output_dir_lineedit)
        output_dir_layout.addWidget(output_dir_browse_button)
        layout.addLayout(output_dir_layout)

        # Extensions
        extensions_label = QLabel("Extensions (comma-separated):")
        extensions_label.setObjectName("extensionsLabel")  # For theming
        self.extensions_lineedit = QLineEdit()
        self.extensions_lineedit.setObjectName("extensionsLineEdit")  # For theming
        extensions_layout = QHBoxLayout()
        extensions_layout.addWidget(extensions_label)
        extensions_layout.addWidget(self.extensions_lineedit)
        layout.addLayout(extensions_layout)

        # System Prompt for Code Analysis
        system_prompt_label = QLabel("System Prompt:")
        system_prompt_label.setObjectName("systemPromptAnalysisLabel")  # For theming
        self.system_prompt_textedit = QTextEdit()
        self.system_prompt_textedit.setObjectName("systemPromptAnalysisTextEdit")  # For theming
        layout.addWidget(system_prompt_label)
        layout.addWidget(self.system_prompt_textedit)

        # Start Analysis Button
        self.start_analysis_button = QPushButton("Start Analysis")
        self.start_analysis_button.setIcon(QIcon(self.icons.get('start', '')))  # Ensure 'start' icon exists
        self.start_analysis_button.setObjectName("startAnalysisButton")  # For theming
        layout.addWidget(self.start_analysis_button)

        # Analysis Results
        self.analysis_results_textedit = QTextEdit()
        self.analysis_results_textedit.setReadOnly(True)
        self.analysis_results_textedit.setObjectName("analysisResultsTextEdit")  # For theming
        layout.addWidget(self.analysis_results_textedit)

        # Connect signals
        self.start_analysis_button.clicked.connect(self.start_analysis)
        input_dir_browse_button.clicked.connect(self.browse_input_directory)
        output_dir_browse_button.clicked.connect(self.browse_output_directory)

    def browse_input_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Input Directory")
        if directory:
            self.input_dir_lineedit.setText(directory)

    def browse_output_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_lineedit.setText(directory)

    def start_analysis(self):
        input_dir = self.input_dir_lineedit.text()
        output_dir = self.output_dir_lineedit.text()
        extensions = self.extensions_lineedit.text()
        system_prompt = self.system_prompt_textedit.toPlainText()

        if not input_dir or not output_dir:
            QMessageBox.warning(self, "Input Error", "Please specify both input and output directories.")
            return

        # Disable the start button and enable the stop button
        self.start_analysis_button.setEnabled(False)
        self.parent.processing_tab.stop_processing_button.setEnabled(True)

        # Show the progress bar and processing log
        self.parent.processing_tab.progress_bar.setVisible(True)
        self.parent.processing_tab.processing_log.setVisible(True)
        self.parent.processing_tab.progress_bar.setValue(0)
        self.parent.processing_tab.processing_log.clear()

        # Create a worker
        self.worker = Worker(input_dir, output_dir, system_prompt, extensions)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.processing_finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_error)

        # Start the worker
        self.worker.start()

    def update_progress(self, item_name, status):
        if item_name == "All Files" and status == "Completed":
            self.parent.processing_tab.progress_bar.setValue(100)
        else:
            current_value = self.parent.processing_tab.progress_bar.value()
            if current_value < 100:
                self.parent.processing_tab.progress_bar.setValue(current_value + 1)
        self.parent.processing_tab.processing_log.append(f"{item_name}: {status}")

    def on_processing_finished(self):
        QMessageBox.information(self, "Processing Complete", "Markdown files have been processed.")
        self.parent.processing_tab.progress_bar.setVisible(False)
        self.parent.processing_tab.processing_log.setVisible(False)
        self.start_analysis_button.setEnabled(True)
        self.parent.processing_tab.stop_processing_button.setEnabled(False)
        self.worker = None

    def on_error(self, error_message):
        QMessageBox.critical(self, "Processing Error", f"An error occurred: {error_message}")
        self.parent.processing_tab.progress_bar.setVisible(False)
        self.parent.processing_tab.processing_log.setVisible(False)
        self.start_analysis_button.setEnabled(True)
        self.parent.processing_tab.stop_processing_button.setEnabled(False)
        self.worker = None
