from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox

from PySide6.QtGui import QIcon
from ai_agent.chat_manager.chat_manager import upload_file, view_files
from log.logger import logger
from PySide6.QtCore import Qt

class FileManagementTab(QWidget):
    def __init__(self, parent=None, icons=None):
        super().__init__(parent)
        self.icons = icons

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # File Management Title
        file_management_title = QLabel("File Management")
        file_management_title.setAlignment(Qt.AlignCenter)
        file_management_title.setObjectName("fileManagementTitle")  # For theming
        layout.addWidget(file_management_title)

        # File Upload Input
        self.upload_file_button = QPushButton("Upload File")
        self.upload_file_button.setIcon(QIcon(self.icons.get('upload', '')))  # Ensure 'upload' icon exists
        self.upload_file_button.setObjectName("uploadFileButton")  # For theming
        self.view_files_button = QPushButton("View Files")
        self.view_files_button.setIcon(QIcon(self.icons.get('view', '')))  # Ensure 'view' icon exists
        self.view_files_button.setObjectName("viewFilesButton")  # For theming
        layout.addWidget(self.upload_file_button)
        layout.addWidget(self.view_files_button)

        # Connect signals
        self.upload_file_button.clicked.connect(self.handle_upload_file)
        self.view_files_button.clicked.connect(self.handle_view_files)

    def handle_upload_file(self):
        try:
            upload_file(self)
            logger.info("File uploaded successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Upload Error", f"Failed to upload file: {str(e)}")
            logger.error(f"Upload Error: {str(e)}")

    def handle_view_files(self):
        try:
            view_files(self)
            logger.info("Viewed files successfully.")
        except Exception as e:
            QMessageBox.critical(self, "View Error", f"Failed to view files: {str(e)}")
            logger.error(f"View Error: {str(e)}")
