# ..\lora_prep.py
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QTextEdit, QFileDialog, 
                               QProgressBar, QTabWidget, QLabel, QSpinBox, QComboBox, QCheckBox, QListWidget, QSplitter,
                               QGroupBox, QScrollArea, QGridLayout, QWizard, QWizardPage, QLineEdit, QTableWidget, QTableWidgetItem,
                               QMessageBox, QDialog, QDialogButtonBox)
from PySide6.QtCore import Qt, QThread, Signal, QSettings, QTimer
from PySide6.QtGui import QFont, QTextCharFormat, QSyntaxHighlighter
import json
import re
import logging
from collections import Counter
from typing import Dict, List, Optional, Union, Any



class DirectoryScanner(QThread):
    filesFound = Signal(list)
    scanningFinished = Signal()

    def __init__(self, directory: str, file_filter, batch_size: int = 50):
        super().__init__()
        self.directory = directory
        self.file_filter = file_filter
        self.batch_size = batch_size

    def run(self):
        batch = []
        for root, _, filenames in os.walk(self.directory):
            path = Path(root)
            if any(ignore in path.parts for ignore in self.file_filter.ignore_list):
                continue
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if self.file_filter.is_valid_file(Path(file_path)):
                    batch.append(file_path)
                    if len(batch) >= self.batch_size:
                        self.filesFound.emit(batch)
                        batch = []
        if batch:
            self.filesFound.emit(batch)
        self.scanningFinished.emit()


class CodeProcessor:
    @staticmethod
    def extract_clean_code(content: str) -> str:
        content = re.sub(r'```[\w]*\n(.*?)```', r'\1', content, flags=re.DOTALL)
        content = re.sub(r'`(.*?)`', r'\1', content)
        content = re.sub(r'#{1,6}\s+.*?\n', '', content)
        content = re.sub(r'\[.*?\]\(.*?\)', '', content)
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
        content = re.sub(r'\*(.*?)\*', r'\1', content)
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        content = re.sub(r'""".*?"""', '', content, flags=re.DOTALL)
        content = re.sub(r"'''.*?'''", '', content, flags=re.DOTALL)
        return content.strip()

    @staticmethod
    def create_training_entry(code: str, 
                              input_text: Optional[str] = None, 
                              metadata: Optional[Dict] = None) -> Dict:
        entry = {'code': code}
        if input_text:
            entry['input'] = input_text
        if metadata:
            entry['metadata'] = metadata
        return entry


class FileFilter:
    DEFAULT_SIZE_MIN = 2
    DEFAULT_SIZE_MAX = 150
    VALID_EXTENSIONS = {
        '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.hpp',
        '.c', '.h', '.cs', '.rb', '.php', '.go', '.rs', '.swift',
        '.kt', '.scala', '.r', '.m', '.json', '.sql'
    }
    DEFAULT_IGNORE_LIST = {
        '__pycache__', '__init__.py', 'main.py', 'config.py', 'settings.py',
        'node_modules', 'package-lock.json', 'package.json',
        '.env', '.gitignore', '.dockerignore',
        'build', 'dist', '.next', 'out',
        '.idea', '.vscode', '.vs',
        'venv', 'env', 'test', 'tests'
    }
    
    def __init__(self):
        self.size_min = self.DEFAULT_SIZE_MIN
        self.size_max = self.DEFAULT_SIZE_MAX
        self.enabled_extensions = self.VALID_EXTENSIONS.copy()
        self.ignore_list = self.DEFAULT_IGNORE_LIST.copy()
        self.remove_comments = False
        self.min_lines = 5
    
    def is_valid_file(self, file_path: Path) -> bool:
        if file_path.suffix not in self.enabled_extensions:
            return False
        try:
            file_size_kb = os.path.getsize(file_path) / 1024
            if self.size_min > 0 and file_size_kb < self.size_min:
                return False
            if self.size_max > 0 and file_size_kb > self.size_max:
                return False
        except OSError:
            return False
        for part in file_path.parts:
            if part in self.ignore_list:
                return False
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content.strip().split('\n')) < self.min_lines:
                    return False
                if all(line.strip().startswith(('#', '//', '/*', '*', '};')) 
                       for line in content.split('\n') if line.strip()):
                    return False
        except Exception:
            return False
        return True


class ProcessingThread(QThread):
    progress = Signal(int)
    status = Signal(str)
    finished = Signal(dict)
    
    def __init__(self, files: List[str], 
                 output_dir: str, 
                 file_filter: FileFilter,
                 include_input: bool = False,
                 include_metadata: bool = False,
                 output_format: str = 'json'):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.file_filter = file_filter
        self.include_input = include_input
        self.include_metadata = include_metadata
        self.output_format = output_format
        
    def run(self):
        processed_data = []
        stats = {'languages': Counter(), 'sizes': [], 'total_lines': 0}
        valid_files = [f for f in self.files if self.file_filter.is_valid_file(Path(f))]
        total = len(valid_files)
        if not total:
            self.status.emit("No valid files found to process!")
            self.finished.emit(stats)
            return
        for i, file_path in enumerate(valid_files, 1):
            try:
                path = Path(file_path)
                size_kb = os.path.getsize(path) / 1024
                self.status.emit(f"Processing {path.name} ({size_kb:.1f}KB)...")
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                clean_code = CodeProcessor.extract_clean_code(content)
                entry = CodeProcessor.create_training_entry(
                    code=clean_code,
                    input_text=path.name if self.include_input else None,
                    metadata={
                        'language': path.suffix.lstrip('.'),
                        'size_kb': size_kb,
                        'lines': len(clean_code.split('\n'))
                    } if self.include_metadata else None
                )
                processed_data.append(entry)
                stats['languages'][path.suffix.lstrip('.')] += 1
                stats['sizes'].append(size_kb)
                stats['total_lines'] += entry.get('metadata', {}).get('lines', 0)
                self.progress.emit(int((i / total) * 100))
            except Exception as e:
                self.status.emit(f"Error processing {file_path}: {str(e)}")
        output_path = Path(self.output_dir) / f"training_data.{self.output_format}"
        with open(output_path, 'w', encoding='utf-8') as f:
            if self.output_format == 'json':
                json.dump(processed_data, f, indent=2)
            else:
                for entry in processed_data:
                    f.write(json.dumps(entry) + '\n')
        self.status.emit(f"Saved {len(processed_data)} entries to {output_path}")
        self.finished.emit(stats)


class CodeHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.formats = {}
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(Qt.blue)
        keyword_format.setFontWeight(QFont.Bold)
        self.formats['keyword'] = keyword_format
        comment_format = QTextCharFormat()
        comment_format.setForeground(Qt.darkGreen)
        self.formats['comment'] = comment_format
        string_format = QTextCharFormat()
        string_format.setForeground(Qt.darkRed)
        self.formats['string'] = string_format
        number_format = QTextCharFormat()
        number_format.setForeground(Qt.darkCyan)
        self.formats['number'] = number_format
        self.keywords = {
            'python': {'import', 'from', 'def', 'class', 'return', 'if', 'else', 'elif',
                       'try', 'except', 'finally', 'for', 'while', 'in', 'is', 'as',
                       'with', 'lambda', 'yield', 'async', 'await'},
            'javascript': {'function', 'var', 'let', 'const', 'if', 'else', 'return',
                           'try', 'catch', 'finally', 'class', 'extends', 'new', 'import',
                           'export', 'default', 'null', 'undefined', 'this', 'super'}
        }
        
    def highlightBlock(self, text):
        self.setFormat(0, len(text), QTextCharFormat())
        for keyword in self.keywords.get('python', set()):
            pattern = f"\\b{keyword}\\b"
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), self.formats['keyword'])
        if text.strip().startswith(('#', '//', '/*')):
            self.setFormat(0, len(text), self.formats['comment'])
        for match in re.finditer(r'\".*?\"|\'.*?\'', text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['string'])
        for match in re.finditer(r'\b\d+\b', text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['number'])


class FilePreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        original_group = QGroupBox("Original Content")
        original_layout = QVBoxLayout()
        self.original_text = QTextEdit()
        self.original_text.setReadOnly(True)
        self.highlighter = CodeHighlighter(self.original_text.document())
        original_layout.addWidget(self.original_text)
        original_group.setLayout(original_layout)
        extracted_group = QGroupBox("Extracted Code Preview")
        extracted_layout = QVBoxLayout()
        self.extracted_text = QTextEdit()
        self.extracted_text.setReadOnly(True)
        self.code_highlighter = CodeHighlighter(self.extracted_text.document())
        extracted_layout.addWidget(self.extracted_text)
        extracted_group.setLayout(extracted_layout)
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(original_group)
        splitter.addWidget(extracted_group)
        layout.addWidget(splitter)
        
    def preview_file(self, file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.original_text.setText(content)
            clean_code = CodeProcessor.extract_clean_code(content)
            self.extracted_text.setText(clean_code)
        except Exception as e:
            self.original_text.setText(f"Error reading file: {str(e)}")
            self.extracted_text.clear()


class DragDropFileList(QListWidget):
    files_dropped = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                files.append(path)
            elif os.path.isdir(path):
                for root, _, filenames in os.walk(path):
                    for filename in filenames:
                        files.append(os.path.join(root, filename))
        if files:
            self.files_dropped.emit(files)


class FileListWidget(QWidget):
    file_selected = Signal(str)
    files_updated = Signal(list)
    
    def __init__(self, file_filter: FileFilter, parent=None):
        super().__init__(parent)
        self.file_filter = file_filter
        layout = QVBoxLayout(self)
        btn_layout = QHBoxLayout()
        self.add_files_btn = QPushButton("Add Files")
        self.add_dir_btn = QPushButton("Add Directory")
        self.remove_btn = QPushButton("Remove Selected")
        self.clear_btn = QPushButton("Clear All")
        btn_layout.addWidget(self.add_files_btn)
        btn_layout.addWidget(self.add_dir_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)
        self.file_list = DragDropFileList()
        layout.addWidget(QLabel("Drag & Drop Files/Folders/Zip Archives Here:"))
        layout.addWidget(self.file_list)
        self.add_files_btn.clicked.connect(self.add_files)
        self.add_dir_btn.clicked.connect(self.add_directory)
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn.clicked.connect(self.clear_files)
        self.file_list.itemSelectionChanged.connect(self.selection_changed)
        self.file_list.files_dropped.connect(self.add_dropped_files)
        self.files = set()
        self.load_file_list()
        
    def save_file_list(self):
        settings = QSettings("LoraPrep", "FileListWidget")
        settings.setValue("file_list", list(self.files))
        
    def load_file_list(self):
        settings = QSettings("LoraPrep", "FileListWidget")
        saved_files = settings.value("file_list", [])
        self.files = set(saved_files)
        self.update_file_list()
        
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files or Zip Archives",
            "",
            f"Files (*{' *'.join(self.file_filter.enabled_extensions)} *.zip)"
        )
        if files:
            self.add_dropped_files(files)
            self.save_file_list()
    
    def add_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if not directory:
            return
        self.scanner = DirectoryScanner(directory, self.file_filter, batch_size=50)
        self.scanner.filesFound.connect(self.add_dropped_files)
        self.scanner.scanningFinished.connect(self.update_file_list)
        self.scanner.scanningFinished.connect(self.save_file_list)
        self.scanner.start()
    
    def add_dropped_files(self, files):
        import zipfile
        temp_extraction_dir = Path(os.getenv("TEMP", "/tmp")) / "lora_prep_extracted"
        temp_extraction_dir.mkdir(exist_ok=True)
        for file in files:
            path_obj = Path(file)
            if path_obj.suffix.lower() == ".zip":
                try:
                    with zipfile.ZipFile(file, 'r') as zf:
                        for zip_info in zf.infolist():
                            inner_path = Path(zip_info.filename)
                            if inner_path.suffix in self.file_filter.enabled_extensions:
                                size_kb = zip_info.file_size / 1024
                                if (self.file_filter.size_min <= size_kb <= self.file_filter.size_max) and zip_info.file_size > 0:
                                    extracted_path = temp_extraction_dir / inner_path.name
                                    with open(extracted_path, 'wb') as fout:
                                        fout.write(zf.read(zip_info.filename))
                                    if self.file_filter.is_valid_file(extracted_path):
                                        self.files.add(str(extracted_path))
                except Exception:
                    pass
            else:
                if self.file_filter.is_valid_file(path_obj):
                    self.files.add(file)
        self.update_file_list()
        self.save_file_list()
        
    def remove_selected(self):
        for item in self.file_list.selectedItems():
            self.files.remove(item.text())
        self.update_file_list()
        self.save_file_list()
        
    def clear_files(self):
        self.files.clear()
        self.update_file_list()
        self.save_file_list()
        
    def update_file_list(self):
        self.file_list.clear()
        for file in sorted(self.files):
            self.file_list.addItem(file)
        self.files_updated.emit(list(self.files))
        
    def selection_changed(self):
        items = self.file_list.selectedItems()
        if items:
            self.file_selected.emit(items[0].text())
            
    def get_files(self) -> List[str]:
        return list(self.files)


class FilterSettingsWidget(QWidget):
    def __init__(self, file_filter: FileFilter, parent=None):
        super().__init__(parent)
        self.file_filter = file_filter
        layout = QVBoxLayout(self)
        size_group = QGroupBox("Size Limits (KB)")
        size_layout = QGridLayout()
        self.min_size = QSpinBox()
        self.min_size.setRange(0, 9999)
        self.min_size.setValue(file_filter.size_min)
        size_layout.addWidget(QLabel("Minimum:"), 0, 0)
        size_layout.addWidget(self.min_size, 0, 1)
        self.max_size = QSpinBox()
        self.max_size.setRange(0, 9999)
        self.max_size.setValue(file_filter.size_max)
        size_layout.addWidget(QLabel("Maximum:"), 1, 0)
        size_layout.addWidget(self.max_size, 1, 1)
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        options_group = QGroupBox("Processing Options")
        options_layout = QVBoxLayout()
        self.remove_comments = QCheckBox("Remove Comments")
        self.remove_comments.setChecked(file_filter.remove_comments)
        options_layout.addWidget(self.remove_comments)
        self.min_lines = QSpinBox()
        self.min_lines.setRange(1, 100)
        self.min_lines.setValue(file_filter.min_lines)
        min_lines_layout = QHBoxLayout()
        min_lines_layout.addWidget(QLabel("Minimum Lines:"))
        min_lines_layout.addWidget(self.min_lines)
        options_layout.addLayout(min_lines_layout)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        ext_group = QGroupBox("File Extensions")
        ext_layout = QVBoxLayout()
        self.ext_checks = {}
        for ext in sorted(FileFilter.VALID_EXTENSIONS):
            cb = QCheckBox(ext)
            cb.setChecked(ext in file_filter.enabled_extensions)
            self.ext_checks[ext] = cb
            ext_layout.addWidget(cb)
        ext_group.setLayout(ext_layout)
        scroll = QScrollArea()
        scroll.setWidget(ext_group)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        self.min_size.valueChanged.connect(self.update_filter)
        self.max_size.valueChanged.connect(self.update_filter)
        self.remove_comments.stateChanged.connect(self.update_filter)
        self.min_lines.valueChanged.connect(self.update_filter)
        for cb in self.ext_checks.values():
            cb.stateChanged.connect(self.update_filter)
            
    def update_filter(self):
        self.file_filter.size_min = self.min_size.value()
        self.file_filter.size_max = self.max_size.value()
        self.file_filter.remove_comments = self.remove_comments.isChecked()
        self.file_filter.min_lines = self.min_lines.value()
        self.file_filter.enabled_extensions = {ext for ext, cb in self.ext_checks.items() if cb.isChecked()}


class MetadataEditorWidget(QWidget):
    metadata_updated = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        fields_group = QGroupBox("Common Fields")
        fields_layout = QGridLayout()
        self.fields = {}
        common_fields = [
            ('description', 'Description'),
            ('language', 'Programming Language'),
            ('category', 'Category'),
            ('difficulty', 'Difficulty Level'),
            ('tags', 'Tags (comma-separated)'),
            ('source', 'Source/Origin'),
            ('author', 'Author/Creator')
        ]
        for i, (field, label) in enumerate(common_fields):
            fields_layout.addWidget(QLabel(f"{label}:"), i, 0)
            self.fields[field] = QLineEdit()
            fields_layout.addWidget(self.fields[field], i, 1)
            self.fields[field].textChanged.connect(self.emit_metadata)
        fields_group.setLayout(fields_layout)
        layout.addWidget(fields_group)
        custom_group = QGroupBox("Custom Fields")
        custom_layout = QVBoxLayout()
        self.custom_fields = QTableWidget(0, 2)
        self.custom_fields.setHorizontalHeaderLabels(['Field Name', 'Value'])
        self.custom_fields.horizontalHeader().setStretchLastSection(True)
        custom_layout.addWidget(self.custom_fields)
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Field")
        remove_btn = QPushButton("Remove Selected")
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        custom_layout.addLayout(btn_layout)
        add_btn.clicked.connect(self.add_custom_field)
        remove_btn.clicked.connect(self.remove_custom_field)
        self.custom_fields.itemChanged.connect(self.emit_metadata)
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)
        
    def add_custom_field(self):
        row = self.custom_fields.rowCount()
        self.custom_fields.insertRow(row)
        self.custom_fields.setItem(row, 0, QTableWidgetItem(""))
        self.custom_fields.setItem(row, 1, QTableWidgetItem(""))
        
    def remove_custom_field(self):
        rows = set(item.row() for item in self.custom_fields.selectedItems())
        for row in sorted(rows, reverse=True):
            self.custom_fields.removeRow(row)
        self.emit_metadata()
        
    def emit_metadata(self):
        metadata = {}
        for field, widget in self.fields.items():
            if widget.text():
                metadata[field] = widget.text()
        for row in range(self.custom_fields.rowCount()):
            name = self.custom_fields.item(row, 0)
            value = self.custom_fields.item(row, 1)
            if name and value and name.text() and value.text():
                metadata[name.text()] = value.text()
        self.metadata_updated.emit(metadata)
        
    def get_metadata(self) -> Dict:
        return self.collect_metadata()
        
    def collect_metadata(self) -> Dict:
        metadata = {}
        for field, widget in self.fields.items():
            if widget.text():
                metadata[field] = widget.text()
        for row in range(self.custom_fields.rowCount()):
            name = self.custom_fields.item(row, 0)
            value = self.custom_fields.item(row, 1)
            if name and value and name.text() and value.text():
                metadata[name.text()] = value.text()
        return metadata


class ProcessingWidget(QWidget):
    processing_complete = Signal(list, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        options_group = QGroupBox("Processing Options")
        options_layout = QVBoxLayout()
        self.include_input = QCheckBox("Include File Name as Input")
        self.include_metadata = QCheckBox("Include File Metadata")
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(['json', 'jsonl'])
        format_layout.addWidget(self.format_combo)
        options_layout.addWidget(self.include_input)
        options_layout.addWidget(self.include_metadata)
        options_layout.addLayout(format_layout)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        layout.addWidget(self.status_text)
        self.process_btn = QPushButton("Process Files")
        layout.addWidget(self.process_btn)
        self.processor = None
        
    def start_processing(self, files: List[str], output_dir: str, 
                         file_filter: FileFilter, metadata: Optional[Dict] = None):
        self.progress_bar.setValue(0)
        self.status_text.clear()
        self.processor = ProcessingThread(
            files=files,
            output_dir=output_dir,
            file_filter=file_filter,
            include_input=self.include_input.isChecked(),
            include_metadata=self.include_metadata.isChecked(),
            output_format=self.format_combo.currentText()
        )
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.status.connect(lambda msg: self.status_text.append(msg))
        self.processor.finished.connect(lambda stats: self.processing_complete.emit(files, stats))
        self.processor.start()
        self.process_btn.setEnabled(False)


class FileSelectionPage(QWizardPage):
    def __init__(self, file_filter: FileFilter, parent=None):
        super().__init__(parent)
        self.file_filter = file_filter
        self.setTitle("Step 1: Select Files")
        layout = QVBoxLayout(self)
        self.file_list_widget = FileListWidget(file_filter)
        self.file_preview = FilePreviewWidget()
        self.file_list_widget.file_selected.connect(self.file_preview.preview_file)
        self.file_list_widget.files_updated.connect(self.completeChanged)
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.file_list_widget)
        splitter.addWidget(self.file_preview)
        layout.addWidget(splitter)
        
    def isComplete(self) -> bool:
        return bool(self.file_list_widget.get_files())
        
    def get_files(self) -> List[str]:
        return self.file_list_widget.get_files()


class PreprocessingPage(QWizardPage):
    def __init__(self, file_filter: FileFilter, parent=None):
        super().__init__(parent)
        self.file_filter = file_filter
        self.setTitle("Step 2: Configure Processing")
        layout = QVBoxLayout(self)
        self.processing_widget = ProcessingWidget()
        layout.addWidget(self.processing_widget)
        self.registerField("include_input", self.processing_widget.include_input)
        self.registerField("include_metadata", self.processing_widget.include_metadata)
        self.registerField("output_format", self.processing_widget.format_combo)
        #self.registerField("output_format*", self.processing_widget.format_combo, "currentText", "currentTextChanged")


class MetadataPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Step 3: Add Metadata (Optional)")
        self.setCommitPage(True)
        layout = QVBoxLayout(self)
        self.metadata_editor = MetadataEditorWidget()
        layout.addWidget(self.metadata_editor)
        preview_group = QGroupBox("Data Preview")
        preview_layout = QVBoxLayout()
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(3)
        self.preview_table.setHorizontalHeaderLabels(['File', 'Code Preview', 'Metadata'])
        preview_layout.addWidget(self.preview_table)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
    def initializePage(self):
        files = self.wizard().get_files()
        include_metadata = self.field("include_metadata")
        self.preview_table.setRowCount(len(files))
        for i, file_path in enumerate(files):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                clean_code = CodeProcessor.extract_clean_code(content)
                metadata = self.metadata_editor.get_metadata() if include_metadata else {}
                self.preview_table.setItem(i, 0, QTableWidgetItem(file_path))
                self.preview_table.setItem(i, 1, QTableWidgetItem(clean_code[:100] + '...' if len(clean_code) > 100 else clean_code))
                self.preview_table.setItem(i, 2, QTableWidgetItem(json.dumps(metadata, indent=2) if metadata else 'No metadata'))
            except Exception as e:
                print(f"Error previewing {file_path}: {str(e)}")
                
    def validatePage(self) -> bool:
        self.wizard().metadata = self.metadata_editor.get_metadata()
        return True


class StatsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.total_files_label = QLabel("Total Files: 0")
        self.total_lines_label = QLabel("Total Lines: 0")
        self.languages_label = QLabel("Languages: None")
        layout.addWidget(self.total_files_label)
        layout.addWidget(self.total_lines_label)
        layout.addWidget(self.languages_label)
        layout.addStretch()
        
    def update_stats(self, stats: dict):
        self.total_files_label.setText(f"Total Files: {stats['total_files']}")
        self.total_lines_label.setText(f"Total Lines: {stats['total_lines']}")
        if stats['languages']:
            lang_text = ", ".join(f"{lang}: {count}" for lang, count in stats['languages'].most_common())
            self.languages_label.setText(f"Languages: {lang_text}")
        else:
            self.languages_label.setText("Languages: None")


class OutputPreviewPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Step 4: Preview and Save")
        layout = QVBoxLayout(self)
        preview_group = QGroupBox("Output Preview")
        preview_layout = QVBoxLayout()
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        stats_group = QGroupBox("Processing Statistics")
        self.stats_widget = StatsWidget()
        stats_layout = QVBoxLayout()
        stats_layout.addWidget(self.stats_widget)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        self.save_btn = QPushButton("Save Output")
        self.save_btn.clicked.connect(self.save_output)
        layout.addWidget(self.save_btn)
        self.processed_data = []
        
    def initializePage(self):
        self.processed_data = []
        files = self.wizard().get_files()
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                clean_code = CodeProcessor.extract_clean_code(content)
                entry = CodeProcessor.create_training_entry(
                    code=clean_code,
                    input_text=file_path if self.field("include_input") else None,
                    metadata=self.wizard().metadata if self.field("include_metadata") else None
                )
                self.processed_data.append(entry)
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
        if self.field("output_format") == 'json':
            preview = json.dumps(self.processed_data, indent=2)
        else:
            preview = '\n'.join(json.dumps(entry) for entry in self.processed_data)
        self.preview_text.setText(preview)
        stats = {
            'total_files': len(self.processed_data),
            'total_lines': sum(len(entry['code'].split('\n')) for entry in self.processed_data),
            'languages': Counter(Path(f).suffix.lstrip('.') for f in files)
        }
        self.stats_widget.update_stats(stats)
        
    def save_output(self):
        if not self.processed_data:
            return
        output_format = str(self.field("output_format"))  # Ensure it's a string
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Output",
            f"training_data.{output_format}",
            f"{output_format.upper()} Files (*.{output_format})"
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                if output_format == 'json':
                    json.dump(self.processed_data, f, indent=2)
                else:
                    for entry in self.processed_data:
                        f.write(json.dumps(entry) + '\n')


class LoraPreprocessingWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LoRA Training Data Preparation")
        self.setWizardStyle(QWizard.ModernStyle)
        self.file_filter = FileFilter()
        self.metadata = {}
        self.file_page = FileSelectionPage(self.file_filter)
        self.addPage(self.file_page)
        self.preprocessing_page = PreprocessingPage(self.file_filter)
        self.addPage(self.preprocessing_page)
        self.metadata_page = MetadataPage()
        self.addPage(self.metadata_page)
        self.output_page = OutputPreviewPage()
        self.addPage(self.output_page)
        self.setMinimumSize(1000, 700)
        
    def get_files(self) -> List[str]:
        return self.file_page.get_files()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LoRA Code Data Preparation")
        self.setMinimumSize(1200, 800)
        self.create_menu_bar()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        toolbar = QHBoxLayout()
        self.new_btn = QPushButton("New Processing")
        self.settings_btn = QPushButton("Settings")
        toolbar.addWidget(self.new_btn)
        toolbar.addWidget(self.settings_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        layout.addWidget(self.tab_widget)
        self.new_btn.clicked.connect(self.start_new_process)
        self.settings_btn.clicked.connect(self.show_settings)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.settings_dialog = None
        self.start_new_process()
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        new_action = file_menu.addAction("New Processing")
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.start_new_process)
        settings_action = file_menu.addAction("Settings")
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)
        
    def start_new_process(self):
        wizard = LoraPreprocessingWizard(self)
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(wizard)
        index = self.tab_widget.addTab(tab, f"Process {self.tab_widget.count() + 1}")
        self.tab_widget.setCurrentIndex(index)
        
    def close_tab(self, index):
        widget = self.tab_widget.widget(index)
        widget.deleteLater()
        self.tab_widget.removeTab(index)
        
    def show_settings(self):
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.show()
        
    def show_about(self):
        QMessageBox.about(self,
                          "About LoRA Code Data Preparation",
                          """
            <h3>LoRA Code Data Preparation Tool</h3>
            <p>A tool for preparing programming code datasets for LoRA fine-tuning.</p>
            <p>Features:</p>
            <ul>
                <li>Code extraction and cleaning</li>
                <li>Flexible metadata handling</li>
                <li>Multiple file processing</li>
                <li>JSON/JSONL output formats</li>
            </ul>
            """)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        layout = QVBoxLayout(self)
        tab_widget = QTabWidget()
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        theme_group = QGroupBox("Theme")
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("UI Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['Dark Orange'])
        theme_layout.addWidget(self.theme_combo)
        theme_group.setLayout(theme_layout)
        general_layout.addWidget(theme_group)
        processing_group = QGroupBox("Processing")
        processing_layout = QVBoxLayout()
        self.parallel_check = QCheckBox("Enable Parallel Processing")
        self.memory_limit = QSpinBox()
        self.memory_limit.setRange(512, 16384)
        self.memory_limit.setValue(2048)
        self.memory_limit.setSuffix(" MB")
        memory_layout = QHBoxLayout()
        memory_layout.addWidget(QLabel("Memory Limit:"))
        memory_layout.addWidget(self.memory_limit)
        processing_layout.addWidget(self.parallel_check)
        processing_layout.addLayout(memory_layout)
        processing_group.setLayout(processing_layout)
        general_layout.addWidget(processing_group)
        file_filter_group = QGroupBox("File Filter Settings")
        file_filter_layout = QVBoxLayout()
        size_limits_layout = QHBoxLayout()
        self.filter_min_size = QSpinBox()
        self.filter_min_size.setRange(0, 9999)
        self.filter_min_size.setValue(2)
        self.filter_max_size = QSpinBox()
        self.filter_max_size.setRange(0, 9999)
        self.filter_max_size.setValue(150)
        size_limits_layout.addWidget(QLabel("Size Minimum (KB):"))
        size_limits_layout.addWidget(self.filter_min_size)
        size_limits_layout.addWidget(QLabel("Size Maximum (KB):"))
        size_limits_layout.addWidget(self.filter_max_size)
        file_filter_layout.addLayout(size_limits_layout)
        ext_group = QGroupBox("File Extensions")
        ext_layout = QVBoxLayout()
        self.ext_checks = {}
        for ext in sorted(FileFilter.VALID_EXTENSIONS):
            cb = QCheckBox(ext)
            cb.setChecked(True)
            self.ext_checks[ext] = cb
            ext_layout.addWidget(cb)
        ext_group.setLayout(ext_layout)
        scroll = QScrollArea()
        scroll.setWidget(ext_group)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(150)
        file_filter_layout.addWidget(scroll)
        file_filter_group.setLayout(file_filter_layout)
        general_layout.addWidget(file_filter_group)
        general_layout.addStretch()
        tab_widget.addTab(general_tab, "General")
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        log_group = QGroupBox("Logging")
        log_layout = QVBoxLayout()
        self.debug_check = QCheckBox("Enable Debug Logging")
        self.log_path = QLineEdit()
        browse_btn = QPushButton("Browse")
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Log File:"))
        path_layout.addWidget(self.log_path)
        path_layout.addWidget(browse_btn)
        log_layout.addWidget(self.debug_check)
        log_layout.addLayout(path_layout)
        log_group.setLayout(log_layout)
        advanced_layout.addWidget(log_group)
        advanced_layout.addStretch()
        tab_widget.addTab(advanced_tab, "Advanced")
        layout.addWidget(tab_widget)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)


class AppSettings:
    def __init__(self):
        self.settings = QSettings('LoraPrep', 'CodeDataPreparation')
        self.init_default_settings()
        
    def init_default_settings(self):
        self.settings.setValue('theme', 'Dark Orange')
        if not self.settings.contains('parallel_processing'):
            self.settings.setValue('parallel_processing', False)
        if not self.settings.contains('memory_limit'):
            self.settings.setValue('memory_limit', 2048)
        if not self.settings.contains('debug_logging'):
            self.settings.setValue('debug_logging', False)
        if not self.settings.contains('log_path'):
            default_log = str(Path.home() / 'lora_prep.log')
            self.settings.setValue('log_path', default_log)
            
    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.value(key, default)
        
    def set(self, key: str, value: Any):
        self.settings.setValue(key, value)
        
    def save(self):
        self.settings.sync()


class AppLogger:
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.setup_logging()
        
    def setup_logging(self):
        level = logging.DEBUG if self.settings.get('debug_logging') else logging.INFO
        log_path = self.settings.get('log_path')
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler()
            ]
        )
        
    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)


class ProcessingSession:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or str(Path.home() / 'lora_training_data')
        self.processed_files = []
        self.stats = {
            'total_files': 0,
            'total_lines': 0,
            'languages': Counter(),
            'errors': []
        }
        
    def add_processed_file(self, file_path: str, entry: Dict):
        self.processed_files.append({
            'file': file_path,
            'entry': entry
        })
        
    def update_stats(self, stats: Dict):
        self.stats.update(stats)
        
    def save_session(self):
        session_file = Path(self.output_dir) / 'session.json'
        os.makedirs(self.output_dir, exist_ok=True)
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump({
                'files': self.processed_files,
                'stats': self.stats
            }, f, indent=2)
            
    @classmethod
    def load_session(cls, session_file: str) -> 'ProcessingSession':
        with open(session_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        session = cls()
        session.processed_files = data['files']
        session.stats = data['stats']
        return session


def setup_exception_handling(logger: logging.Logger):
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.excepthook = handle_exception


def main():
    settings = AppSettings()
    app_logger = AppLogger(settings)
    logger = app_logger.get_logger('main')
    setup_exception_handling(logger)
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
