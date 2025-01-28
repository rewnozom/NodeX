# ./search_tab.py

import os
import sys
import glob
import json
import ast

from PySide6.QtCore import Qt, Signal, QMimeData, QPoint
from PySide6.QtGui import QFont, QAction, QKeySequence, QDrag, QIcon, QColor, QLinearGradient, QPalette
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QLabel, QFrame, QScrollArea,
    QCheckBox, QInputDialog, QGridLayout, QGroupBox, QComboBox
)

from frontend.Pages.desktop.Layout.Dashboard.utils.theme_utils import apply_dark_theme
from frontend.Pages.desktop.Layout.Dashboard.utils.card_utils import create_card

IS_PHONE = False  # Adjust as needed

class StyledButton(QPushButton):
    def __init__(self, text, color="#B22222", font_size=12, icon_path=None):
        super().__init__(text)

        if icon_path:
            self.setIcon(QIcon(icon_path))

class SearchFieldWidget(QFrame):
    itemAdded = Signal(str, str)
    itemRemoved = Signal(str, str)
    fieldRemoved = Signal(str)
    
    def __init__(self, field_id, field_name, swap_words=False, swap_sites=False,
                 swap_words_before="", swap_words_after="", swap_sites_before="", swap_sites_after=""):
        super().__init__()
        self.field_id = field_id
        self.field_name = field_name
        self.swap_words = swap_words
        self.swap_sites = swap_sites
        self.swap_words_before = swap_words_before
        self.swap_words_after = swap_words_after
        self.swap_sites_before = swap_sites_before
        self.swap_sites_after = swap_sites_after
        self.tags = []  # New attribute for tag management
        self.setAcceptDrops(True)
        self.initUI()
    
    def initUI(self):
        font_size = 12 if not IS_PHONE else 10
        checkbox_font_size = 12 if not IS_PHONE else 10
        button_font_size = 12 if not IS_PHONE else 10
        label_font = QFont("Arial", font_size, QFont.Bold)
        

        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        
        header_layout = QHBoxLayout()
        self.name_label = QLabel(self.field_name)
        self.name_label.setFont(label_font)
        header_layout.addWidget(self.name_label)
        header_layout.addStretch()
        
        edit_btn = StyledButton("✎", font_size=button_font_size)
        edit_btn.setToolTip("Edit field name")
        edit_btn.clicked.connect(self.edit_name)
        edit_btn.setFixedSize(40, 40)
        header_layout.addWidget(edit_btn)
        
        copy_btn = StyledButton("📋", font_size=button_font_size)
        copy_btn.setToolTip("Copy field content")
        copy_btn.clicked.connect(self.copy_content)
        copy_btn.setFixedSize(40, 40)
        header_layout.addWidget(copy_btn)
        
        # Tag editor button
        tag_btn = StyledButton("🏷️", font_size=button_font_size)
        tag_btn.setToolTip("Edit tags")
        tag_btn.clicked.connect(self.edit_tags)
        tag_btn.setFixedSize(40, 40)
        header_layout.addWidget(tag_btn)
        
        delete_btn = StyledButton("🗑️", font_size=button_font_size)
        delete_btn.setToolTip("Delete this field")
        delete_btn.clicked.connect(self.delete_field)
        delete_btn.setFixedSize(40, 40)
        header_layout.addWidget(delete_btn)
        
        main_layout.addLayout(header_layout)
        
        # Customization area (for swap settings)
        customization_group = QGroupBox("Customizations")

        customization_layout = QGridLayout()
        customization_layout.setSpacing(10)
        
        self.swap_words_checkbox = QCheckBox("Swap Words")
        self.swap_words_checkbox.setChecked(self.swap_words)
        self.swap_words_checkbox.stateChanged.connect(self.toggle_swap_words)
        self.swap_words_before_input = QLineEdit()
        self.swap_words_before_input.setPlaceholderText("Before Words")
        self.swap_words_before_input.setText(self.swap_words_before)
        self.swap_words_before_input.setEnabled(self.swap_words)
        self.swap_words_after_input = QLineEdit()
        self.swap_words_after_input.setPlaceholderText("After Words")
        self.swap_words_after_input.setText(self.swap_words_after)
        self.swap_words_after_input.setEnabled(self.swap_words)
        
        self.swap_sites_checkbox = QCheckBox("Swap Sites")
        self.swap_sites_checkbox.setChecked(self.swap_sites)
        self.swap_sites_checkbox.stateChanged.connect(self.toggle_swap_sites)
        self.swap_sites_before_input = QLineEdit()
        self.swap_sites_before_input.setPlaceholderText("Before Sites")
        self.swap_sites_before_input.setText(self.swap_sites_before)
        self.swap_sites_before_input.setEnabled(self.swap_sites)
        self.swap_sites_after_input = QLineEdit()
        self.swap_sites_after_input.setPlaceholderText("After Sites")
        self.swap_sites_after_input.setText(self.swap_sites_after)
        self.swap_sites_after_input.setEnabled(self.swap_sites)
        
        customization_layout.addWidget(self.swap_words_checkbox, 0, 0)
        customization_layout.addWidget(QLabel("Before:"), 0, 1)
        customization_layout.addWidget(self.swap_words_before_input, 0, 2)
        customization_layout.addWidget(QLabel("After:"), 0, 3)
        customization_layout.addWidget(self.swap_words_after_input, 0, 4)
        customization_layout.addWidget(self.swap_sites_checkbox, 1, 0)
        customization_layout.addWidget(QLabel("Before:"), 1, 1)
        customization_layout.addWidget(self.swap_sites_before_input, 1, 2)
        customization_layout.addWidget(QLabel("After:"), 1, 3)
        customization_layout.addWidget(self.swap_sites_after_input, 1, 4)
        
        customization_group.setLayout(customization_layout)
        main_layout.addWidget(customization_group)
        
        # List for items
        self.item_list = QListWidget()
        main_layout.addWidget(self.item_list)
        
        # Input for new items
        input_layout = QHBoxLayout()
        self.item_input = QLineEdit()
        self.item_input.setPlaceholderText("Enter word or URL")
        self.item_input.returnPressed.connect(self.add_item)
        input_layout.addWidget(self.item_input)
        add_btn = StyledButton("➕", font_size=button_font_size)
        add_btn.setToolTip("Add item")
        add_btn.clicked.connect(self.add_item)
        add_btn.setFixedSize(40, 40)
        input_layout.addWidget(add_btn)
        main_layout.addLayout(input_layout)
        
        self.setLayout(main_layout)
    
    def toggle_swap_words(self, state):
        enabled = state == Qt.Checked
        self.swap_words_before_input.setEnabled(enabled)
        self.swap_words_after_input.setEnabled(enabled)
    
    def toggle_swap_sites(self, state):
        enabled = state == Qt.Checked
        self.swap_sites_before_input.setEnabled(enabled)
        self.swap_sites_after_input.setEnabled(enabled)
    
    def add_item(self):
        item = self.item_input.text().strip()
        if not item:
            QMessageBox.warning(self, "Empty Input", "Please enter a word or URL.")
            return
        if "." in item:
            if self.swap_sites_checkbox.isChecked():
                before = self.swap_sites_before_input.text()
                after = self.swap_sites_after_input.text()
                new_item = f"{before}site:{item}{after}"
            else:
                new_item = f"site:{item}"
        else:
            if self.swap_words_checkbox.isChecked():
                before = self.swap_words_before_input.text()
                after = self.swap_words_after_input.text()
                new_item = f"{before}{item}{after}"
            else:
                new_item = f'"{item}"'
        if self.item_list.findItems(new_item, Qt.MatchExactly):
            QMessageBox.warning(self, "Duplicate", f'"{new_item}" already exists.')
        else:
            list_item = QListWidgetItem(new_item)
            list_item.setFlags(list_item.flags() | Qt.ItemIsEditable)
            self.item_list.addItem(list_item)
            self.itemAdded.emit(self.field_id, new_item)
        self.item_input.clear()
    
    def edit_name(self):
        new_name, ok = QInputDialog.getText(self, "Edit Field Name", "New name:", QLineEdit.Normal, self.field_name)
        if ok and new_name:
            self.field_name = new_name
            self.name_label.setText(new_name)
    
    def copy_content(self):
        items = [self.item_list.item(i).text() for i in range(self.item_list.count())]
        QApplication.clipboard().setText(" ".join(items))
    
    def delete_field(self):
        reply = QMessageBox.question(self, 'Delete Field', f"Delete '{self.field_name}'?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.fieldRemoved.emit(self.field_id)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            for item in self.item_list.selectedItems():
                self.itemRemoved.emit(self.field_id, item.text())
                self.item_list.takeItem(self.item_list.row(item))
        else:
            super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.position().toPoint()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if (event.position().toPoint() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.field_id)
        drag.setMimeData(mime_data)
        pixmap = self.grab()
        drag.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
        drag.exec(Qt.MoveAction)
    
    def edit_tags(self):
        current_tags_str = ", ".join(self.tags)
        new_tags_str, ok = QInputDialog.getText(self, "Edit Tags", "Enter comma separated tags:", text=current_tags_str)
        if ok:
            self.tags = [t.strip() for t in new_tags_str.split(",") if t.strip()]
            QMessageBox.information(self, "Tags Updated", f"Tags: {', '.join(self.tags)}")

class SearchTab(QWidget):
    """
    The Search Fields tab containing a list of search fields,
    along with a toolbox panel for internal filtering.
    """
    def __init__(self, json_directory="././frontend/Pages/desktop/Layout/Dashboard/Dashboard/json/"):
        super().__init__()
        self.json_directory = json_directory
        self.ensure_directory_exists()
        self.json_files = sorted(glob.glob(os.path.join(self.json_directory, "search_fields*.json")))
        if not self.json_files:
            self.json_files = [os.path.join(self.json_directory, "search_fields.json")]
            with open(self.json_files[0], "w") as f:
                json.dump([], f, indent=4)
        self.current_file_index = 0
        self.search_fields = []
        self.history = []
        self.history_index = -1
        self.initUI()
        self.load_data(self.json_files[self.current_file_index])
    
    def ensure_directory_exists(self):
        os.makedirs(self.json_directory, exist_ok=True)
    
    def initUI(self):
        main_layout = QVBoxLayout(self)
        apply_dark_theme(self)
        
        # Upper area: Search Fields and Controls
        fields_container = QWidget()
        fields_layout = QHBoxLayout(fields_container)
        fields_layout.setSpacing(10)
        
        # Left-side control panel
        left_panel = QFrame()

        left_panel.setFixedWidth(250)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        add_field_btn = StyledButton("➕ Add New Search Field", font_size=12)
        add_field_btn.setToolTip("Add a new search field")
        add_field_btn.clicked.connect(self.add_search_field)
        left_layout.addWidget(add_field_btn)
        load_btn = StyledButton("📂 Load JSON", font_size=12)
        load_btn.setToolTip("Load from JSON")
        load_btn.clicked.connect(lambda: self.load_data(self.json_files[self.current_file_index]))
        left_layout.addWidget(load_btn)
        add_page_btn = StyledButton("➕ Add New Page", font_size=12)
        add_page_btn.setToolTip("Add a new page")
        add_page_btn.clicked.connect(self.add_page)
        left_layout.addWidget(add_page_btn)
        remove_page_btn = StyledButton("🗑️ Remove Page", font_size=12)
        remove_page_btn.setToolTip("Remove current page")
        remove_page_btn.clicked.connect(self.remove_current_page)
        left_layout.addWidget(remove_page_btn)
        undo_btn = StyledButton("↩️ Undo", font_size=12)
        undo_btn.setToolTip("Undo (Ctrl+Z)")
        undo_btn.clicked.connect(self.undo)
        left_layout.addWidget(undo_btn)
        redo_btn = StyledButton("↪️ Redo", font_size=12)
        redo_btn.setToolTip("Redo (Ctrl+Y)")
        redo_btn.clicked.connect(self.redo)
        left_layout.addWidget(redo_btn)
        left_layout.addStretch()
        
        fields_layout.addWidget(left_panel)
        
        # Right-side: Search Fields display
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        if IS_PHONE:
            self.fields_layout = QVBoxLayout(scroll_content)
        else:
            from PySide6.QtWidgets import QGridLayout
            self.fields_layout = QGridLayout(scroll_content)
            self.fields_layout.setSpacing(20)
        scroll_area.setWidget(scroll_content)
        right_layout.addWidget(scroll_area)
        
        # Global search input in right panel
        global_search_layout = QHBoxLayout()
        self.global_search_input = QLineEdit()
        self.global_search_input.setPlaceholderText("Search across fields...")
        self.global_search_input.returnPressed.connect(self.search_term)
        global_search_layout.addWidget(self.global_search_input)
        search_btn = StyledButton("🔍 Search", font_size=12)
        search_btn.clicked.connect(self.search_term)
        global_search_layout.addWidget(search_btn)
        right_layout.addLayout(global_search_layout)
        
        fields_layout.addWidget(right_panel)
        
        main_layout.addWidget(fields_container)
        
        # Toolbox Panel for filtering by tag
        toolbox_panel = QFrame()

        toolbox_layout = QHBoxLayout(toolbox_panel)
        toolbox_layout.setSpacing(10)
        filter_label = QLabel("Filter by Tag:")
        toolbox_layout.addWidget(filter_label)
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Enter tag...")
        toolbox_layout.addWidget(self.filter_input)
        filter_btn = StyledButton("Apply Filter", font_size=12)
        filter_btn.clicked.connect(self.apply_filter)
        toolbox_layout.addWidget(filter_btn)
        clear_filter_btn = StyledButton("Clear Filter", font_size=12)
        clear_filter_btn.clicked.connect(self.clear_filter)
        toolbox_layout.addWidget(clear_filter_btn)
        main_layout.addWidget(toolbox_panel)
    
    def add_search_field(self):
        field_id = str(len(self.search_fields))
        field_name = f"Search Field {len(self.search_fields) + 1}"
        widget = SearchFieldWidget(field_id, field_name)
        widget.itemAdded.connect(self.on_item_added)
        widget.itemRemoved.connect(self.on_item_removed)
        widget.fieldRemoved.connect(self.on_field_removed)
        if IS_PHONE:
            self.fields_layout.addWidget(widget)
        else:
            row, col = divmod(len(self.search_fields), 2)
            self.fields_layout.addWidget(widget, row, col)
        self.search_fields.append({
            "id": field_id,
            "name": field_name,
            "items": [],
            "swap_words": False,
            "swap_sites": False,
            "swap_words_before": "",
            "swap_words_after": "",
            "swap_sites_before": "",
            "swap_sites_after": "",
            "tags": []
        })
        self.update_history()
        self.save_data()
    
    def on_item_added(self, field_id, item):
        for field in self.search_fields:
            if field["id"] == field_id:
                field["items"].append(item)
                break
        self.update_history()
        self.save_data()
    
    def on_item_removed(self, field_id, item):
        for field in self.search_fields:
            if field["id"] == field_id:
                field["items"].remove(item)
                break
        self.update_history()
        self.save_data()
    
    def on_field_removed(self, field_id):
        for i, field in enumerate(self.search_fields):
            if field["id"] == field_id:
                del self.search_fields[i]
                break
        self.refresh_ui()
        self.update_history()
        self.save_data()
    
    def update_history(self):
        self.history = self.history[:self.history_index + 1]
        self.history.append(json.loads(json.dumps(self.search_fields)))
        self.history_index += 1
    
    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.search_fields = json.loads(json.dumps(self.history[self.history_index]))
            self.refresh_ui()
            self.save_data()
        else:
            QMessageBox.information(self, "Info", "Nothing to undo.")
    
    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.search_fields = json.loads(json.dumps(self.history[self.history_index]))
            self.refresh_ui()
            self.save_data()
        else:
            QMessageBox.information(self, "Info", "Nothing to redo.")
    
    def refresh_ui(self):
        for i in reversed(range(self.fields_layout.count())):
            widget = self.fields_layout.itemAt(i).widget()
            if widget:
                self.fields_layout.removeWidget(widget)
                widget.deleteLater()
        for idx, field in enumerate(self.search_fields):
            widget = SearchFieldWidget(
                field["id"], field["name"],
                swap_words=field.get("swap_words", False),
                swap_sites=field.get("swap_sites", False),
                swap_words_before=field.get("swap_words_before", ""),
                swap_words_after=field.get("swap_words_after", ""),
                swap_sites_before=field.get("swap_sites_before", ""),
                swap_sites_after=field.get("swap_sites_after", "")
            )
            widget.tags = field.get("tags", [])
            widget.itemAdded.connect(self.on_item_added)
            widget.itemRemoved.connect(self.on_item_removed)
            widget.fieldRemoved.connect(self.on_field_removed)
            for item in field["items"]:
                li = QListWidgetItem(item)
                li.setFlags(li.flags() | Qt.ItemIsEditable)
                widget.item_list.addItem(li)
            if IS_PHONE:
                self.fields_layout.addWidget(widget)
            else:
                row, col = divmod(idx, 2)
                self.fields_layout.addWidget(widget, row, col)
    
    def save_data(self):
        file_name = self.json_files[self.current_file_index]
        try:
            with open(file_name, "w") as f:
                json.dump(self.search_fields, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def load_data(self, file_name=None):
        if file_name is None:
            file_name = self.json_files[self.current_file_index]
        try:
            with open(file_name, "r") as f:
                self.search_fields = json.load(f)
            self.refresh_ui()
            self.update_history()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def apply_filter(self):
        tag = self.filter_input.text().strip().lower()
        if not tag:
            QMessageBox.warning(self, "Empty Filter", "Enter a tag to filter.")
            return
        filtered = [field for field in self.search_fields if "tags" in field and any(tag == t.lower() for t in field["tags"])]
        if not filtered:
            QMessageBox.information(self, "No Results", f"No fields found with tag '{tag}'.")
        else:
            self.search_fields = filtered
            self.refresh_ui()
    
    def clear_filter(self):
        self.filter_input.clear()
        self.load_data(self.json_files[self.current_file_index])
    
    def add_page(self):
        new_index = len(self.json_files)
        new_file = os.path.join(self.json_directory, f"search_fields_{new_index}.json")
        try:
            with open(new_file, "w") as f:
                json.dump([], f, indent=4)
            self.json_files.append(new_file)
            self.current_file_index = new_index
            self.load_data(new_file)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def remove_current_page(self):
        if len(self.json_files) <= 1:
            QMessageBox.warning(self, "Warning", "At least one page must exist.")
            return
        current = self.json_files[self.current_file_index]
        reply = QMessageBox.question(self, "Remove Page", f"Remove page '{current}'?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                os.remove(current)
                self.json_files.pop(self.current_file_index)
                if self.current_file_index >= len(self.json_files):
                    self.current_file_index = len(self.json_files) - 1
                self.load_data(self.json_files[self.current_file_index])
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def search_term(self):
        term = self.global_search_input.text().strip()
        if not term:
            QMessageBox.warning(self, "Empty Search", "Enter a search term.")
            return
        matching = []
        for field in self.search_fields:
            for item in field["items"]:
                if term.lower() in item.lower():
                    matching.append(field["name"])
                    break
        if matching:
            QMessageBox.information(self, "Results", f"Found in fields:\n" + "\n".join(matching))
        else:
            QMessageBox.information(self, "Results", "No matching fields found.")
    
    @staticmethod
    def extract_imports_and_functions(code: str):
        tree = ast.parse(code)
        imports = []
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else ""))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                names = ', '.join([alias.name + (f" as {alias.asname}" if alias.asname else "") for alias in node.names])
                level = '.' * node.level
                imports.append(f"from {level}{module} import {names}")
            elif isinstance(node, ast.FunctionDef):
                code_snippet = ast.get_source_segment(code, node)
                if code_snippet:
                    functions.append(code_snippet)
        return imports, functions

class SearchTabWrapper(QWidget):
    """
    A wrapper for the search tab to be used in the main dashboard.
    """
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.tab = SearchTab()
        layout.addWidget(self.tab)
