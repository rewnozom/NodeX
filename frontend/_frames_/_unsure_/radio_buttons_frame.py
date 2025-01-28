from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QFileDialog, 
    QMessageBox
)
from ui.widgets.custom_buttons import CustomButton
from frontend.Theme.fonts import Fonts
from Utils.Enums.enums import ThemeColors

# Now copy the RadiobuttonFrame class from gui.py here

class RadiobuttonFrame(QFrame):
    csv_file_selected = Signal(str)
    csv_output_selected = Signal(str)
    markdown_file_selected = Signal(str)
    markdown_output_selected = Signal(str)
    reverse_csv_triggered = Signal()
    reverse_markdown_triggered = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_paths = {}
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Initialize the UI components"""
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        
        # Header
        self.header_label = QLabel("Reverse Extraction:")
        self.header_label.setFont(Fonts.get_bold(12))
        self.layout.addWidget(self.header_label)
        
        # CSV Controls
        self.select_csv_button = CustomButton("Select CSV File")
        self.select_csv_output_button = CustomButton("Select Output Directory")
        self.reverse_csv_button = CustomButton("Reverse CSV Extraction")
        
        self.layout.addWidget(self.select_csv_button)
        self.layout.addWidget(self.select_csv_output_button)
        self.layout.addWidget(self.reverse_csv_button)
        
        # Markdown Controls
        self.select_markdown_button = CustomButton("Select Markdown File")
        self.select_markdown_output_button = CustomButton("Select Output Directory")
        self.reverse_markdown_button = CustomButton("Reverse Markdown Extraction")
        
        self.layout.addWidget(self.select_markdown_button)
        self.layout.addWidget(self.select_markdown_output_button)
        self.layout.addWidget(self.reverse_markdown_button)
        
        self.layout.addStretch()
        
        # Frame styling
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.PRIMARY.value};
                border: 1px solid {ThemeColors.TERTIARY.value};
                border-radius: 4px;
            }}
            QLabel {{
                color: {ThemeColors.TEXT_PRIMARY.value};
            }}
        """)

    def setup_connections(self):
        """Setup signal connections"""
        self.select_csv_button.clicked.connect(self.open_file_dialog_csv)
        self.select_csv_output_button.clicked.connect(self.open_directory_dialog_csv)
        self.reverse_csv_button.clicked.connect(self.run_reverse_csv)
        
        self.select_markdown_button.clicked.connect(self.open_file_dialog_markdown)
        self.select_markdown_output_button.clicked.connect(self.open_directory_dialog_markdown)
        self.reverse_markdown_button.clicked.connect(self.run_reverse_markdown)

    def open_file_dialog_csv(self):
        """Open file dialog for CSV selection"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "Excel Files (*.xlsx)"
        )
        if file_path:
            self.selected_paths['csv_file'] = file_path
            self.csv_file_selected.emit(file_path)

    def open_directory_dialog_csv(self):
        """Open directory dialog for CSV output"""
        directory = QFileDialog.getExistingDirectory(self, "Select CSV Output Directory")
        if directory:
            self.selected_paths['csv_output'] = directory
            self.csv_output_selected.emit(directory)

    def open_file_dialog_markdown(self):
        """Open file dialog for Markdown selection"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Markdown File",
            "",
            "Markdown Files (*.md)"
        )
        if file_path:
            self.selected_paths['markdown_file'] = file_path
            self.markdown_file_selected.emit(file_path)

    def open_directory_dialog_markdown(self):
        """Open directory dialog for Markdown output"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Markdown Output Directory"
        )
        if directory:
            self.selected_paths['markdown_output'] = directory
            self.markdown_output_selected.emit(directory)

    def run_reverse_csv(self):
        """Execute reverse CSV extraction"""
        if 'csv_file' not in self.selected_paths or 'csv_output' not in self.selected_paths:
            QMessageBox.warning(
                self,
                "Missing Selection",
                "Please select both a CSV file and an output directory."
            )
            return
        
        self.reverse_csv_triggered.emit()

    def run_reverse_markdown(self):
        """Execute reverse Markdown extraction"""
        if 'markdown_file' not in self.selected_paths or 'markdown_output' not in self.selected_paths:
            QMessageBox.warning(
                self,
                "Missing Selection",
                "Please select both a Markdown file and an output directory."
            )
            return
        
        self.reverse_markdown_triggered.emit()

    def get_selected_paths(self) -> dict:
        """Get all currently selected paths"""
        return self.selected_paths.copy()

    def clear_selections(self):
        """Clear all selected paths"""
        self.selected_paths.clear()

