# ./_markdown_csv_extractor/components/BottomControls.py

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLineEdit, QPushButton, QLabel, QProgressBar
from PySide6.QtGui import QFont
from ..Theme import ThemeColors
from ..GUI_Constants_and_Settings import SettingsManager
import os
from PySide6.QtCore import (
    Qt, Signal, QObject, QTimer, QThread, Slot,
    QPoint, QPropertyAnimation, QEasingCurve
)
from PySide6.QtGui import (
    QFont, QPalette, QColor, QKeyEvent
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea, QLineEdit,
    QFileDialog, QMessageBox, QCheckBox, QProgressBar,
    QListWidget, QSizePolicy, QInputDialog, QComboBox, QSplitter, QScrollerProperties, QScroller
)

class BottomControls(QFrame):
    run_clicked = Signal()
    
    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setup_ui()

    def setup_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Path display
        self.current_path = QLineEdit()
        self.current_path.setReadOnly(True)
        self.current_path.setPlaceholderText("Select working directory...")
        self.current_path.setText(
            self.settings_manager.get_setting("paths", "base_dir", "")
        )
        self.current_path.setCursor(Qt.PointingHandCursor)
        self.current_path.mousePressEvent = lambda event: self.select_directory()
        layout.addWidget(self.current_path)

        # Progress frame
        self.progress_frame = QFrame()
        progress_layout = QVBoxLayout(self.progress_frame)

        # CSV Progress
        self.csv_progress_label = QLabel("CSV Progress:")
        self.csv_progress = QProgressBar()
        self.csv_status = QLabel("")
        progress_layout.addWidget(self.csv_progress_label)
        progress_layout.addWidget(self.csv_progress)
        progress_layout.addWidget(self.csv_status)

        # Markdown Progress
        self.markdown_progress_label = QLabel("Markdown Progress:")
        self.markdown_progress = QProgressBar()
        self.markdown_status = QLabel("")
        progress_layout.addWidget(self.markdown_progress_label)
        progress_layout.addWidget(self.markdown_progress)
        progress_layout.addWidget(self.markdown_status)

        self.progress_frame.hide()

        # Run button
        self.run_button = QPushButton("Run")
        self.run_button.setMinimumHeight(48)
        self.run_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.ACCENT};
                font-size: 16px;
                font-weight: bold;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.ACCENT_HOVER};
            }}
        """)
        self.run_button.clicked.connect(self.run_clicked.emit)
        layout.addWidget(self.run_button)

        # Footer
        footer = QLabel("By: Tobias Raanaes | Version 1.0.0")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #A1A1AA;")  # zinc-400
        layout.addWidget(footer)

        # Add widgets to layout
        layout.addWidget(self.progress_frame)

        # Styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.SECONDARY};
                border-top: 1px solid {ThemeColors.BORDER};
            }}
        """)

    def select_directory(self):
        """Handle directory selection"""
        print("BottomControls: Selecting working directory")  # Debug
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Working Directory",
            self.current_path.text()
        )
        if directory:
            relative_directory = self.settings_manager.absolute_to_relative(directory)
            self.current_path.setText(directory)
            self.settings_manager.update_setting("paths", "base_dir", relative_directory)

            # Auto-set output directory
            output_dir = os.path.join(directory, 'output')
            relative_output_dir = self.settings_manager.absolute_to_relative(output_dir)
            self.settings_manager.update_setting("paths", "output_dir", relative_output_dir)

            print(f"BottomControls: Working directory set to {relative_directory}")  # Debug

    def show_progress(self):
        """Show progress bars"""
        self.progress_frame.show()
        self.run_button.setEnabled(False)
        self.csv_progress.setValue(0)
        self.markdown_progress.setValue(0)
        self.csv_progress_label.show()
        self.csv_progress.show()
        self.csv_status.show()
        self.markdown_progress_label.show()
        self.markdown_progress.show()
        self.markdown_status.show()
        print("BottomControls: Progress bars shown")  # Debug

    def hide_progress(self):
        """Hide progress bars and reset"""
        self.progress_frame.hide()
        self.run_button.setEnabled(True)
        self.csv_progress_label.hide()
        self.csv_progress.hide()
        self.csv_status.hide()
        self.markdown_progress_label.hide()
        self.markdown_progress.hide()
        self.markdown_status.hide()
        print("BottomControls: Progress bars hidden")  # Debug

    def update_progress(self, extraction_type: str, value: int):
        """Update progress bar value"""
        if extraction_type == "CSV":
            self.csv_progress.setValue(value)
            print(f"BottomControls: CSV Progress updated to {value}%")  # Debug
        else:
            self.markdown_progress.setValue(value)
            print(f"BottomControls: Markdown Progress updated to {value}%")  # Debug

    def update_status(self, extraction_type: str, status: str):
        """Update status message"""
        if extraction_type == "CSV":
            self.csv_status.setText(status)
            print(f"BottomControls: CSV Status updated to '{status}'")  # Debug
        else:
            self.markdown_status.setText(status)
            print(f"BottomControls: Markdown Status updated to '{status}'")  # Debug
