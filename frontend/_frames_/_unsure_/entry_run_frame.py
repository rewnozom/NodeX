import os

from PySide6.QtCore import Signal, Qt, QThread
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QPushButton, QLineEdit, 
    QFileDialog, QMessageBox, QLabel, QProgressBar,
    QSizePolicy
)
from Utils.Enums.enums import ThemeColors
from frontend.Theme.fonts import Fonts
from backends.workers.extraction_worker import ExtractionWorker
from backends.workers.extraction_manager import ExtractionManager

class EntryRunFrame(QFrame):
    """Frame containing path entry and run button"""
    run_triggered = Signal()
    extraction_progress = Signal(str, int)  # type, progress value
    extraction_status = Signal(str, str)    # type, status message
    
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()
        self.setup_connections()
        self.active_workers = {}
        
        # Set initial directory to base_dir from settings
        base_dir = self.settings_manager.get_setting("paths", "base_dir", "")
        if base_dir:
            self.entry_path.setText(base_dir)

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        # Path entry
        self.entry_path = QLineEdit()
        self.entry_path.setPlaceholderText("Click to select directory...")
        self.entry_path.setFont(Fonts.get_default(10))
        self.entry_path.setReadOnly(True)
        self.entry_path.setCursor(Qt.PointingHandCursor)
        self.layout.addWidget(self.entry_path)
        
        # Run button
        self.run_button = QPushButton("Run")
        self.run_button.setFont(Fonts.get_bold(10))
        self.run_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.layout.addWidget(self.run_button)

        # Add progress bars
        self.progress_layout = QVBoxLayout()
        
        # CSV Progress
        self.csv_progress_label = QLabel("CSV Progress:")
        self.csv_progress = QProgressBar()
        self.csv_status = QLabel("")
        self.progress_layout.addWidget(self.csv_progress_label)
        self.progress_layout.addWidget(self.csv_progress)
        self.progress_layout.addWidget(self.csv_status)
        
        # Markdown Progress
        self.markdown_progress_label = QLabel("Markdown Progress:")
        self.markdown_progress = QProgressBar()
        self.markdown_status = QLabel("")
        self.progress_layout.addWidget(self.markdown_progress_label)
        self.progress_layout.addWidget(self.markdown_progress)
        self.progress_layout.addWidget(self.markdown_status)
        
        self.layout.addLayout(self.progress_layout)
        
        # Initially hide progress bars
        self.csv_progress_label.hide()
        self.csv_progress.hide()
        self.csv_status.hide()
        self.markdown_progress_label.hide()
        self.markdown_progress.hide()
        self.markdown_status.hide()

        # Styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.PRIMARY.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 4px;
            }}
            QLineEdit {{
                background-color: {ThemeColors.SECONDARY_BACKGROUND.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                padding: 8px;
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 4px;
            }}
            QLineEdit:hover {{
                border-color: {ThemeColors.HOVER_BUTTONS.value};
            }}
            QPushButton {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
                color: {ThemeColors.TEXT_PRIMARY.value};
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.HOVER_BUTTONS.value};
            }}
            QPushButton:pressed {{
                background-color: {ThemeColors.PRIMARY_BUTTONS.value};
            }}
        """)

    def setup_connections(self):
        self.entry_path.mousePressEvent = self.open_file_dialog
        self.run_button.clicked.connect(self.run_command)

    def open_file_dialog(self, event):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            self.entry_path.text() or ""
        )
        if directory:
            self.entry_path.setText(directory)
            self.settings_manager.update_setting('paths', 'base_dir', directory)
            output_dir = os.path.join(directory, 'output')
            self.settings_manager.update_setting('paths', 'output_dir', output_dir)

    def run_command(self):
        from backends.Extractorz import CSVEx, MarkdownEx
        if not self.entry_path.text():
            QMessageBox.warning(self, "No Directory Selected", "Please select a directory first.")
            return

        selected_path = self.entry_path.text()
        output_path = os.path.join(selected_path, 'output')
        print(f"Running extraction from path: {selected_path}")

        # Access the main App window to get the checkbox_frame
        main_window = self.window()
        if not hasattr(main_window, 'checkbox_frame'):
            QMessageBox.critical(
                self,
                "Internal Error",
                "Checkbox frame not found in the main window."
            )
            return

        checkbox_frame = main_window.checkbox_frame
        extraction_started = False

        # Initialize ExtractionManager
        self.extraction_manager = ExtractionManager()
        self.extraction_manager.all_finished.connect(self.on_all_extractions_finished)

        # Start CSV extraction if selected
        if checkbox_frame.extract_csv:
            self.csv_progress_label.show()
            self.csv_progress.show()
            self.csv_status.show()
            self.csv_progress.setValue(0)
            
            thread = QThread()
            worker = ExtractionWorker(CSVEx, selected_path, output_path, main_window.settings_path)
            
            worker.moveToThread(thread)
            self.setup_worker_connections(worker, thread, "CSV")
            
            thread.started.connect(worker.run)
            thread.start()
            
            self.active_workers["CSV"] = (worker, thread)
            extraction_started = True

        # Start Markdown extraction if selected
        if checkbox_frame.extract_markdown:
            self.markdown_progress_label.show()
            self.markdown_progress.show()
            self.markdown_status.show()
            self.markdown_progress.setValue(0)
            
            thread = QThread()
            worker = ExtractionWorker(MarkdownEx, selected_path, output_path, main_window.settings_path)
            
            worker.moveToThread(thread)
            self.setup_worker_connections(worker, thread, "Markdown")
            
            thread.started.connect(worker.run)
            thread.start()
            
            self.active_workers["Markdown"] = (worker, thread)
            extraction_started = True

        if not extraction_started:
            QMessageBox.information(
                self,
                "No Extraction Selected",
                "Please select at least one extraction option."
            )
            return

    def setup_worker_connections(self, worker, thread, worker_type):
        # Connect progress and status signals
        worker.progress.connect(lambda v: self.update_progress(worker_type, v))
        worker.status.connect(lambda s: self.update_status(worker_type, s))
        
        # Connect completion and error signals
        worker.finished.connect(lambda: self.handle_extraction_finished(worker_type))
        worker.error.connect(lambda e: self.handle_extraction_error(worker_type, e))
        
        # Connect cleanup signals
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)

    def update_progress(self, extraction_type, value):
        if extraction_type == "CSV":
            self.csv_progress.setValue(value)
        else:
            self.markdown_progress.setValue(value)

    def update_status(self, extraction_type, message):
        if extraction_type == "CSV":
            self.csv_status.setText(message)
        else:
            self.markdown_status.setText(message)

    def handle_extraction_finished(self, extraction_type):
        # Remove from active workers
        if extraction_type in self.active_workers:
            worker, thread = self.active_workers.pop(extraction_type)
            
        # Check if all extractions are complete
        if not self.active_workers:
            self.run_button.setEnabled(True)
            QMessageBox.information(
                self,
                "Extraction Complete",
                "All selected extractions have completed successfully."
            )
            self.run_triggered.emit()

    def handle_extraction_error(self, extraction_type, error_message):
        QMessageBox.critical(
            self,
            f"{extraction_type} Extraction Error",
            f"An error occurred during {extraction_type} extraction:\n{error_message}"
        )
        
        # Clean up the failed worker
        if extraction_type in self.active_workers:
            worker, thread = self.active_workers.pop(extraction_type)
            worker.stop()
            thread.quit()
            
        # Re-enable run button if no other extractions are running
        if not self.active_workers:
            self.run_button.setEnabled(True)

    def on_all_extractions_finished(self):
        QMessageBox.information(
            self,
            "Extraction Completed",
            "All extraction processes have been completed successfully."
        )
        self.run_triggered.emit()
