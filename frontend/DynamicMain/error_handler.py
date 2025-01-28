# dynamic_main/error_handler.py

from PySide6.QtWidgets import QMessageBox
from log.logger import logger

class ErrorHandler:
    def __init__(self, main_window):
        self.main_window = main_window

    def show_error_message(self, message: str, details: str = ""):

        msg_box = QMessageBox(QMessageBox.Critical, "Error", message, parent=self.main_window)
        if details:
            msg_box.setDetailedText(details)
        msg_box.exec()
