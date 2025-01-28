# pages/qframes/InputFrame/InputFrame.py

import os
from typing import Tuple
from PySide6.QtWidgets import QFrame, QVBoxLayout, QTextEdit, QPushButton, QLabel, QHBoxLayout, QMessageBox, QFileDialog, QInputDialog
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QDropEvent, QDragEnterEvent, QKeyEvent
from .._helper.Worker import WorkerThread
from .._helper.CodeBlockExtractor import CodeBlockExtractor

class InputFrame(QFrame):
    """
    Handles text input, drag-and-drop, and processing of text, files, and URLs.
    """
    # Define signals to communicate with other frames
    processing_complete = Signal(list)  # Emits list of CodeAnalysisResult
    error_occurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.extractor = CodeBlockExtractor()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Text Input Area
        self.textEdit = QTextEdit()
        self.textEdit.setPlaceholderText("Paste your text here and press Ctrl+Enter to process...")
        self.textEdit.installEventFilter(self)
        layout.addWidget(self.textEdit)

        # Drag-and-Drop Label
        drag_drop_label = QLabel("Or drag and drop files/folders here")
        drag_drop_label.setAlignment(Qt.AlignCenter)
        drag_drop_label.setStyleSheet("QLabel { border: 2px dashed #aaa; padding: 20px; }")
        layout.addWidget(drag_drop_label)

        # Buttons for processing
        buttons_layout = QHBoxLayout()
        self.processButton = QPushButton('Process Text')
        self.processButton.clicked.connect(self.processText)
        self.processFileButton = QPushButton('Process Files/Folders')
        self.processFileButton.clicked.connect(self.processFiles)
        self.processURLButton = QPushButton('Process URL')
        self.processURLButton.clicked.connect(self.processURL)
        buttons_layout.addWidget(self.processButton)
        buttons_layout.addWidget(self.processFileButton)
        buttons_layout.addWidget(self.processURLButton)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def eventFilter(self, obj, event):
        """
        Handles key events, such as Ctrl+Enter for processing text.
        """
        if obj is self.textEdit and event.type() == QEvent.KeyPress:
            if isinstance(event, QKeyEvent):  # Check if it's a key event
                if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                    self.processText()
                    return True
        return super().eventFilter(obj, event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        Handles the drag enter event for drag-and-drop functionality.
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """
        Handles the drop event for drag-and-drop functionality.
        """
        urls = event.mimeData().urls()
        file_paths = [url.toLocalFile() for url in urls]
        for path in file_paths:
            if os.path.isfile(path) or os.path.isdir(path):
                self.processPath(path)
        event.acceptProposedAction()

    def processPath(self, path: str):
        """
        Initiates processing of a dropped file or directory.
        """
        if os.path.isfile(path) or os.path.isdir(path):
            processing_function = self.extractor.process_file if os.path.isfile(path) else self.extractor.process_directory
            worker = WorkerThread(processing_function, path)
            worker.signals.result.connect(self.handleResults)
            worker.signals.error.connect(self.showError)
            worker.start()

    def processFiles(self):
        """
        Opens a file dialog to select files or directories for processing.
        """
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setOption(QFileDialog.DontUseNativeDialog, False)
        dialog.setNameFilters(["Text Files (*.txt)", "Markdown Files (*.md)", "HTML Files (*.html)", "All Files (*)"])
        if dialog.exec():
            file_paths = dialog.selectedFiles()
            for path in file_paths:
                self.processPath(path)

    def processText(self):
        """
        Processes text entered in the text input area.
        """
        text = self.textEdit.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "No Text", "Please enter some text to process.")
            return
        worker = WorkerThread(self.extractor.process_text, text)
        worker.signals.result.connect(self.handleResults)
        worker.signals.error.connect(self.showError)
        worker.start()

    def processURL(self):
        """
        Prompts the user to enter a URL and processes the web page content.
        """
        url, ok = self.getTextInput("Process URL", "Enter the URL to process:")
        if ok and url:
            worker = WorkerThread(self.extractor.process_url, url)
            worker.signals.result.connect(self.handleResults)
            worker.signals.error.connect(self.showError)
            worker.start()

    def getTextInput(self, title: str, label: str) -> Tuple[str, bool]:
        """
        Prompts the user to enter text input via a dialog.
        """
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, title, label)
        return text, ok

    def handleResults(self, results: list):
        """
        Handles the results returned from the worker thread.
        """
        if not results:
            QMessageBox.information(self, "No Code Blocks", "No code blocks were found in the input.")
            return
        self.processing_complete.emit(results)

    def showError(self, message: str):
        """
        Emits an error signal to be handled by the main page.
        """
        self.error_occurred.emit(message)
