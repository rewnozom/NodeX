# terminal_widget.py

import sys
import subprocess
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QLineEdit
from PySide6.QtCore import Qt, Signal, Slot, QProcess

class TerminalWidget(QWidget):
    """
    A simple terminal widget using PySide6.
    """
    output_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.process = None
        self.init_process()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Display area
        self.output_area = QPlainTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet("background-color: black; color: white; font-family: Consolas;")
        layout.addWidget(self.output_area)

        # Input area
        self.input_line = QLineEdit()
        self.input_line.setStyleSheet("background-color: #333333; color: white; font-family: Consolas;")
        self.input_line.returnPressed.connect(self.execute_command)
        layout.addWidget(self.input_line)

        # Connect the output signal
        self.output_signal.connect(self.display_output)

    def init_process(self):
        """Initialize the subprocess to run shell commands."""
        try:
            if sys.platform.startswith('win'):
                # Use cmd.exe on Windows
                self.process = subprocess.Popen("cmd.exe", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            else:
                # Use bash on Unix-like systems
                self.process = subprocess.Popen("/bin/bash", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

            # Start threads to read stdout and stderr
            import threading
            threading.Thread(target=self.read_stdout, daemon=True).start()
            threading.Thread(target=self.read_stderr, daemon=True).start()
        except Exception as e:
            self.display_output(f"Error initializing shell: {e}\n")

    def read_stdout(self):
        """Read standard output from the subprocess."""
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.output_signal.emit(line)
                else:
                    break
        except Exception as e:
            self.output_signal.emit(f"Error reading stdout: {e}\n")

    def read_stderr(self):
        """Read standard error from the subprocess."""
        try:
            for line in iter(self.process.stderr.readline, ''):
                if line:
                    self.output_signal.emit(line)
                else:
                    break
        except Exception as e:
            self.output_signal.emit(f"Error reading stderr: {e}\n")

    @Slot()
    def execute_command(self):
        """Execute the command entered by the user."""
        command = self.input_line.text()
        if not command.strip():
            return
        self.display_output(f"> {command}\n")
        self.input_line.clear()

        if self.process:
            try:
                self.process.stdin.write(command + '\n')
                self.process.stdin.flush()
            except Exception as e:
                self.display_output(f"Error sending command: {e}\n")
        else:
            self.display_output("Shell process not initialized.\n")

    @Slot(str)
    def display_output(self, text):
        """Display output in the terminal."""
        self.output_area.appendPlainText(text)
        # Auto-scroll to the bottom
        self.output_area.verticalScrollBar().setValue(self.output_area.verticalScrollBar().maximum())

    def closeEvent(self, event):
        """Handle widget close event to terminate the subprocess."""
        if self.process:
            self.process.terminate()
            self.process.wait()
        super().closeEvent(event)
