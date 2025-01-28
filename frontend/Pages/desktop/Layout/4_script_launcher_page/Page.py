# ./frontend/pages/2_script_launcher_page.py
import os
import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, 
    QMessageBox, QScrollArea, QFrame, QHBoxLayout
)
from PySide6.QtCore import Qt, QThread, QObject, Signal
from PySide6.QtGui import QIcon

from Config.AppConfig.icon_config import ICONS


# ------------------- WorkerThread Class ------------------- #

class WorkerThread(QThread):
    """
    Worker thread for running scripts to keep the GUI responsive.
    """
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.function(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    finished = Signal()
    error = Signal(str)
    result = Signal(object)


# ------------------- Page Class ------------------- #

class Page(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # Header frame
        self.header_frame = QFrame()
        header_layout = QVBoxLayout(self.header_frame)
        self.title = QLabel("Script Launcher")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setObjectName("pageTitle")  # For theming
        header_layout.addWidget(self.title)
        main_layout.addWidget(self.header_frame)

        # Main content frame
        self.content_frame = QFrame()
        content_layout = QVBoxLayout(self.content_frame)

        # Create a scroll area for buttons
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setObjectName("scriptScrollArea")  # For theming
        content_layout.addWidget(self.scroll_area)

        # Create a widget to hold the buttons
        self.button_container = QWidget()
        self.button_layout = QVBoxLayout(self.button_container)
        self.button_container.setObjectName("buttonContainer")  # For theming
        self.scroll_area.setWidget(self.button_container)

        # Search for scripts
        script_dir = './scripts/'
        supported_extensions = ['.ahk', '.ps1', '.ini', '.isi']

        for root, dirs, files in os.walk(script_dir):
            for file in files:
                if any(file.endswith(ext) for ext in supported_extensions):
                    script_path = os.path.join(root, file)
                    self.create_script_button(self.button_layout, script_path)

        main_layout.addWidget(self.content_frame)

        # Footer frame
        self.footer_frame = QFrame()
        footer_layout = QHBoxLayout(self.footer_frame)
        self.version_label = QLabel("Version: 1.0.0")
        self.version_label.setObjectName("versionLabel")  # For theming
        footer_layout.addWidget(self.version_label, alignment=Qt.AlignRight)
        main_layout.addWidget(self.footer_frame)

        # Assign object names for theming
        self.set_object_names()

    def set_object_names(self):
        # Main widget
        self.setObjectName("scriptPage")

        # Frames
        self.header_frame.setObjectName("headerFrame")
        self.content_frame.setObjectName("contentFrame")
        self.footer_frame.setObjectName("footerFrame")

        # Labels
        self.title.setObjectName("pageTitle")
        self.version_label.setObjectName("versionLabel")

        # Scroll area and container
        self.scroll_area.setObjectName("scriptScrollArea")
        self.button_container.setObjectName("buttonContainer")

        # Style existing buttons by assigning object names
        for button in self.findChildren(QPushButton):
            button.setProperty("class", "scriptButton")
            button.setObjectName(f"{button.text().replace(' ', '')}Button")  # e.g., "RunScript1Button"

    def create_script_button(self, layout, script_path):
        script_name = os.path.basename(script_path)
        button = QPushButton(f"Run {script_name}")
        button.setProperty("class", "scriptButton")
        button.setObjectName(f"run{script_name.replace('.', '')}Button")  # For theming
        button.clicked.connect(lambda checked, path=script_path: self.run_script(path))
        layout.addWidget(button, alignment=Qt.AlignCenter)

    def run_script(self, script_path):
        try:
            if script_path.endswith('.ahk'):
                subprocess.Popen(['autohotkey', script_path])
            elif script_path.endswith('.ps1'):
                subprocess.Popen(['powershell', '-ExecutionPolicy', 'Bypass', '-File', script_path])
            elif script_path.endswith(('.ini', '.isi')):
                subprocess.Popen([script_path], shell=True)
            else:
                raise ValueError("Unsupported script type")
            QMessageBox.information(self, "Success", f"Executing {script_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run {script_path}: {str(e)}")

    def on_load(self):
        # Optional: Actions to perform when the page is loaded
        pass

    def on_unload(self):
        # Optional: Actions to perform when the page is unloaded
        pass
