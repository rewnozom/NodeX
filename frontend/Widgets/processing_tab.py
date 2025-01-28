from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QProgressBar, QTextEdit, QMessageBox

from PySide6.QtGui import QIcon
from ai_agent.chat_manager.chat_manager import process_files
from ai_agent.threads.worker_thread import Worker
from frontend._frames_._helper.workers import FileProcessingWorker, WorkerSignals
from log.logger import logger

class ProcessingTab(QWidget):
    def __init__(self, parent=None, icons=None):
        super().__init__(parent)
        self.icons = icons
        self.worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Process Markdown Files Button
        self.start_processing_button = QPushButton("Process Markdown Files")
        self.start_processing_button.setIcon(QIcon(self.icons.get('process', '')))  # Ensure 'process' icon exists
        self.start_processing_button.setObjectName("startProcessingButton")  # For theming
        layout.addWidget(self.start_processing_button)

        # Stop Button Below the Process Button
        self.stop_processing_button = QPushButton("Stop Processing")
        self.stop_processing_button.setIcon(QIcon(self.icons.get('stop', '')))  # Ensure 'stop' icon exists
        self.stop_processing_button.setObjectName("stopProcessingButton")  # For theming
        self.stop_processing_button.setEnabled(False)  # Initially disabled
        layout.addWidget(self.stop_processing_button)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setObjectName("processingProgressBar")  # For theming
        layout.addWidget(self.progress_bar)

        # Processing Log
        self.processing_log = QTextEdit()
        self.processing_log.setReadOnly(True)
        self.processing_log.setVisible(False)
        self.processing_log.setObjectName("processingLog")  # For theming
        layout.addWidget(self.processing_log)

        # Add stretch to push widgets to the top
        layout.addStretch()

        # Connect signals
        self.start_processing_button.clicked.connect(self.start_processing)
        self.stop_processing_button.clicked.connect(self.stop_processing)

    def start_processing(self):
        self.start_processing_button.setEnabled(False)
        self.stop_processing_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.processing_log.setVisible(True)
        self.progress_bar.setValue(0)
        self.processing_log.clear()

        self.worker = Worker()
        self.worker.progress_update.connect(self.update_progress)
        self.worker.processing_finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_error)

        self.worker.start()

    def stop_processing(self):
        if self.worker:
            self.worker.stop()
            self.processing_log.append("Stopping processing...")
            self.stop_processing_button.setEnabled(False)

    def update_progress(self, item_name, status):
        if item_name == "All Files" and status == "Completed":
            self.progress_bar.setValue(100)
        else:
            current_value = self.progress_bar.value()
            if current_value < 100:
                self.progress_bar.setValue(current_value + 1)
        self.processing_log.append(f"{item_name}: {status}")

    def on_processing_finished(self):
        QMessageBox.information(self, "Processing Complete", "Markdown files have been processed.")
        self.progress_bar.setVisible(False)
        self.processing_log.setVisible(False)
        self.start_processing_button.setEnabled(True)
        self.stop_processing_button.setEnabled(False)
        self.worker = None

    def on_error(self, error_message):
        QMessageBox.critical(self, "Processing Error", f"An error occurred: {error_message}")
        self.progress_bar.setVisible(False)
        self.processing_log.setVisible(False)
        self.start_processing_button.setEnabled(True)
        self.stop_processing_button.setEnabled(False)
        self.worker = None
