# ./_dashboard_notes_.py

import os
import sys
import ast
import glob
import json

from PySide6.QtCore import Qt, Signal, QMimeData, QPoint
from PySide6.QtGui import QColor, QLinearGradient, QPalette, QFont, QAction, QKeySequence, QDrag, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QLabel, QFrame, QScrollArea, QCheckBox, QInputDialog, QGridLayout,
    QGroupBox, QComboBox, QSizePolicy, QSpacerItem
)

# Import our theme and card utilities
from frontend.Pages.desktop.Layout.Dashboard.utils.theme_utils import apply_dark_theme
from frontend.Pages.desktop.Layout.Dashboard.utils.card_utils import create_card

def add_project_subdirectories_to_syspath(root_dir):
    """
    Recursively add all subdirectories of the project root to sys.path.
    """
    for dirpath, dirnames, _ in os.walk(root_dir):
        if dirpath not in sys.path:
            sys.path.insert(0, dirpath)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
add_project_subdirectories_to_syspath(project_root)

IS_PHONE = False  # Set to True for phone design, False for desktop design

class StyledButton(QPushButton):
    def __init__(self, text, color="#B22222", font_size=12, icon_path=None):
        super().__init__(text)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: 2px solid #8B0000;
                padding: 5px 10px;
                border-radius: 5px;
                font-weight: bold;
                font-size: {font_size}px;
            }}
            QPushButton:hover {{
                background-color: #FF0000;
            }}
            QPushButton:pressed {{
                background-color: #CC0000;
            }}
        """)
        if icon_path and os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))


class TitleBar(QWidget):
    """
    Custom title bar for a frameless window.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QWidget {
                background-color: #1C1C1C;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
            }
            QPushButton {
                border: none;
                background-color: transparent;
                color: #FFFFFF;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        self.initUI()
        self.start = QPoint(0, 0)
        self.pressing = False

    def initUI(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)
        self.title_label = QLabel("Search Field Dashboard")
        self.title_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.title_label)
        layout.addStretch()
        self.minimize_btn = QPushButton("—")
        self.minimize_btn.setFixedSize(30, 30)
        self.minimize_btn.clicked.connect(self.minimize_window)
        layout.addWidget(self.minimize_btn)
        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setFixedSize(30, 30)
        self.maximize_btn.clicked.connect(self.maximize_restore_window)
        layout.addWidget(self.maximize_btn)
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.close_window)
        layout.addWidget(self.close_btn)
        self.setLayout(layout)

    def minimize_window(self):
        self.parent.showMinimized()

    def maximize_restore_window(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.maximize_btn.setText("□")
        else:
            self.parent.showMaximized()
            self.maximize_btn.setText("❐")

    def close_window(self):
        self.parent.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start = self.mapToGlobal(event.position().toPoint())
            self.pressing = True

    def mouseMoveEvent(self, event):
        if self.pressing:
            self.parent.move(self.mapToGlobal(event.position().toPoint()) - self.start + self.parent.pos())
            self.start = self.mapToGlobal(event.position().toPoint())

    def mouseReleaseEvent(self, event):
        self.pressing = False


class SearchFieldWidget(QFrame):
    itemAdded = Signal(str, str)
    itemRemoved = Signal(str, str)
    fieldRemoved = Signal(str)

    def __init__(self, field_id, field_name, swap_words=False, swap_sites=False,
                 swap_words_before="", swap_words_after="",
                 swap_sites_before="", swap_sites_after=""):
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
        if IS_PHONE:
            font_size = 10
            checkbox_font_size = 10
            button_font_size = 10
            label_font = QFont("Arial", 10, QFont.Bold)
        else:
            font_size = 12
            checkbox_font_size = 12
            button_font_size = 12
            label_font = QFont("Arial", 12, QFont.Bold)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: #2E2E2E;
                border: 2px solid #555;
                border-radius: 10px;
                padding: 10px;
            }}
            QLabel {{
                color: #FFFFFF;
                font-size: {font_size}px;
                background: transparent;
            }}
            QListWidget {{
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555;
                border-radius: 5px;
                font-size: {font_size}px;
            }}
            QLineEdit {{
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 5px;
                font-size: {font_size}px;
            }}
            QCheckBox {{
                color: #FFFFFF;
                font-size: {checkbox_font_size}px;
            }}
        """)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(5 if IS_PHONE else 10)

        header_layout = QHBoxLayout()
        self.name_label = QLabel(self.field_name)
        self.name_label.setFont(label_font)
        header_layout.addWidget(self.name_label)
        header_layout.addStretch()

        edit_btn = StyledButton("✎", font_size=button_font_size)
        edit_btn.setToolTip("Edit field name")
        edit_btn.clicked.connect(self.edit_name)
        edit_btn.setFixedSize(30 if IS_PHONE else 40, 30 if IS_PHONE else 40)
        header_layout.addWidget(edit_btn)

        copy_btn = StyledButton("📋", font_size=button_font_size)
        copy_btn.setToolTip("Copy field content")
        copy_btn.clicked.connect(self.copy_content)
        copy_btn.setFixedSize(30 if IS_PHONE else 40, 30 if IS_PHONE else 40)
        header_layout.addWidget(copy_btn)

        # New tag editor button
        tag_btn = StyledButton("🏷️", font_size=button_font_size)
        tag_btn.setToolTip("Edit tags")
        tag_btn.clicked.connect(self.edit_tags)
        tag_btn.setFixedSize(30 if IS_PHONE else 40, 30 if IS_PHONE else 40)
        header_layout.addWidget(tag_btn)

        delete_btn = StyledButton("🗑️", font_size=button_font_size)
        delete_btn.setToolTip("Delete this field")
        delete_btn.clicked.connect(self.delete_field)
        delete_btn.setFixedSize(30 if IS_PHONE else 40, 30 if IS_PHONE else 40)
        header_layout.addWidget(delete_btn)

        main_layout.addLayout(header_layout)

        customization_group = QGroupBox("Customizations" if not IS_PHONE else "Custom")
        customization_group.setStyleSheet(f"""
            QGroupBox {{
                color: #FFFFFF;
                font-size: {font_size}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 5px;
            }}
        """)
        customization_layout = QGridLayout()
        customization_layout.setSpacing(5 if IS_PHONE else 10)

        self.swap_words_checkbox = QCheckBox("Swap Words" if not IS_PHONE else "Swap Wds")
        self.swap_words_checkbox.setChecked(self.swap_words)
        self.swap_words_checkbox.stateChanged.connect(self.toggle_swap_words)
        self.swap_words_before_input = QLineEdit()
        self.swap_words_before_input.setPlaceholderText("Before Words" if not IS_PHONE else "B Words")
        self.swap_words_before_input.setText(self.swap_words_before)
        self.swap_words_before_input.setEnabled(self.swap_words)
        self.swap_words_after_input = QLineEdit()
        self.swap_words_after_input.setPlaceholderText("After Words" if not IS_PHONE else "A Words")
        self.swap_words_after_input.setText(self.swap_words_after)
        self.swap_words_after_input.setEnabled(self.swap_words)
        self.swap_sites_checkbox = QCheckBox("Swap Sites" if not IS_PHONE else "Swap Sts")
        self.swap_sites_checkbox.setChecked(self.swap_sites)
        self.swap_sites_checkbox.stateChanged.connect(self.toggle_swap_sites)
        self.swap_sites_before_input = QLineEdit()
        self.swap_sites_before_input.setPlaceholderText("Before Sites" if not IS_PHONE else "B Sites")
        self.swap_sites_before_input.setText(self.swap_sites_before)
        self.swap_sites_before_input.setEnabled(self.swap_sites)
        self.swap_sites_after_input = QLineEdit()
        self.swap_sites_after_input.setPlaceholderText("After Sites" if not IS_PHONE else "A Sites")
        self.swap_sites_after_input.setText(self.swap_sites_after)
        self.swap_sites_after_input.setEnabled(self.swap_sites)

        customization_layout.addWidget(self.swap_words_checkbox, 0, 0)
        customization_layout.addWidget(QLabel("Before:" if not IS_PHONE else "B:"), 0, 1)
        customization_layout.addWidget(self.swap_words_before_input, 0, 2)
        customization_layout.addWidget(QLabel("After:" if not IS_PHONE else "A:"), 0, 3)
        customization_layout.addWidget(self.swap_words_after_input, 0, 4)
        customization_layout.addWidget(self.swap_sites_checkbox, 1, 0)
        customization_layout.addWidget(QLabel("Before:" if not IS_PHONE else "B:"), 1, 1)
        customization_layout.addWidget(self.swap_sites_before_input, 1, 2)
        customization_layout.addWidget(QLabel("After:" if not IS_PHONE else "A:"), 1, 3)
        customization_layout.addWidget(self.swap_sites_after_input, 1, 4)
        customization_group.setLayout(customization_layout)
        main_layout.addWidget(customization_group)

        self.item_list = QListWidget()
        main_layout.addWidget(self.item_list)

        input_layout = QHBoxLayout()
        self.item_input = QLineEdit()
        self.item_input.setPlaceholderText("Enter word or URL")
        self.item_input.setToolTip("Enter word or URL")
        self.item_input.returnPressed.connect(self.add_item)
        input_layout.addWidget(self.item_input)
        add_btn = StyledButton("➕", font_size=button_font_size)
        add_btn.setToolTip("Add item")
        add_btn.clicked.connect(self.add_item)
        add_btn.setFixedSize(30 if IS_PHONE else 40, 30 if IS_PHONE else 40)
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
        is_site = "." in item
        if is_site:
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
            QMessageBox.warning(self, "Duplicate", f'"{new_item}" already exists in this search field.')
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
        reply = QMessageBox.question(self, 'Delete Field', f"Are you sure you want to delete '{self.field_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
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
        # Simple comma-separated tag editor.
        current_tags_str = ", ".join(self.tags)
        new_tags_str, ok = QInputDialog.getText(self, "Edit Tags", "Enter tags (comma separated):", text=current_tags_str)
        if ok:
            self.tags = [tag.strip() for tag in new_tags_str.split(",") if tag.strip()]
            QMessageBox.information(self, "Tags Updated", f"Current tags: {', '.join(self.tags)}")


class PromptVaultWidget(QWidget):
    """
    A widget for managing an AI prompt vault with categorized prompts.
    """
    promptsUpdated = Signal(dict)

    def __init__(self, json_path="./frontend/Pages/desktop/Layout/Dashboard/Dashboard/prompt_vault.json", parent=None):
        super().__init__(parent)
        self.json_path = json_path
        self.data = {}  # Structure: {category: [prompt, ...]}
        self.load_data()
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        header_label = QLabel("AI Prompt Vault")
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        main_layout.addWidget(header_label)

        # Categories card
        category_card = create_card("Categories")
        card_layout = category_card.layout()
        cat_layout = QHBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.currentIndexChanged.connect(self.refresh_prompt_list)
        cat_layout.addWidget(self.category_combo)
        add_cat_btn = StyledButton("➕", font_size=12)
        add_cat_btn.setToolTip("Add new category")
        add_cat_btn.clicked.connect(self.add_category)
        cat_layout.addWidget(add_cat_btn)
        edit_cat_btn = StyledButton("✎", font_size=12)
        edit_cat_btn.setToolTip("Edit current category")
        edit_cat_btn.clicked.connect(self.edit_category)
        cat_layout.addWidget(edit_cat_btn)
        del_cat_btn = StyledButton("🗑️", font_size=12)
        del_cat_btn.setToolTip("Delete current category")
        del_cat_btn.clicked.connect(self.delete_category)
        cat_layout.addWidget(del_cat_btn)
        card_layout.addLayout(cat_layout)
        main_layout.addWidget(category_card)

        # Prompts card
        prompt_card = create_card("Prompts")
        prompt_layout = prompt_card.layout()
        self.prompt_list = QListWidget()
        self.prompt_list.setSelectionMode(QListWidget.SingleSelection)
        prompt_layout.addWidget(self.prompt_list)
        input_layout = QHBoxLayout()
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Enter prompt text here...")
        self.prompt_input.setStyleSheet("""
            QLineEdit {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 5px;
            }
        """)
        input_layout.addWidget(self.prompt_input)
        add_prompt_btn = StyledButton("Add Prompt", font_size=12)
        add_prompt_btn.clicked.connect(self.add_prompt)
        input_layout.addWidget(add_prompt_btn)
        edit_prompt_btn = StyledButton("Edit Prompt", font_size=12)
        edit_prompt_btn.clicked.connect(self.edit_prompt)
        input_layout.addWidget(edit_prompt_btn)
        remove_prompt_btn = StyledButton("Remove Prompt", font_size=12)
        remove_prompt_btn.clicked.connect(self.remove_prompt)
        input_layout.addWidget(remove_prompt_btn)
        prompt_layout.addLayout(input_layout)
        main_layout.addWidget(prompt_card)

        self.setLayout(main_layout)
        self.refresh_category_combo()

    def refresh_category_combo(self):
        current = self.category_combo.currentText()
        self.category_combo.clear()
        categories = list(self.data.keys())
        if not categories:
            self.data["Default"] = []
            categories = ["Default"]
        self.category_combo.addItems(categories)
        if current in categories:
            index = categories.index(current)
            self.category_combo.setCurrentIndex(index)
        self.refresh_prompt_list()

    def refresh_prompt_list(self):
        self.prompt_list.clear()
        category = self.category_combo.currentText()
        if category and category in self.data:
            for prompt in self.data[category]:
                item = QListWidgetItem(prompt)
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                self.prompt_list.addItem(item)

    def add_category(self):
        text, ok = QInputDialog.getText(self, "Add Category", "Category Name:")
        if ok and text:
            if text in self.data:
                QMessageBox.warning(self, "Duplicate Category", f"Category '{text}' already exists.")
                return
            self.data[text] = []
            self.refresh_category_combo()
            self.save_data()
            self.promptsUpdated.emit(self.data)

    def edit_category(self):
        current = self.category_combo.currentText()
        if not current:
            return
        new_text, ok = QInputDialog.getText(self, "Edit Category", "New Category Name:", text=current)
        if ok and new_text and new_text != current:
            if new_text in self.data:
                QMessageBox.warning(self, "Duplicate Category", f"Category '{new_text}' already exists.")
                return
            self.data[new_text] = self.data.pop(current)
            self.refresh_category_combo()
            self.save_data()
            self.promptsUpdated.emit(self.data)

    def delete_category(self):
        current = self.category_combo.currentText()
        if not current:
            return
        if QMessageBox.question(self, "Delete Category", f"Are you sure you want to delete category '{current}'?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            del self.data[current]
            self.refresh_category_combo()
            self.save_data()
            self.promptsUpdated.emit(self.data)

    def add_prompt(self):
        category = self.category_combo.currentText()
        prompt_text = self.prompt_input.text().strip()
        if not prompt_text:
            QMessageBox.warning(self, "Empty Prompt", "Please enter prompt text.")
            return
        self.data[category].append(prompt_text)
        self.prompt_input.clear()
        self.refresh_prompt_list()
        self.save_data()
        self.promptsUpdated.emit(self.data)

    def edit_prompt(self):
        category = self.category_combo.currentText()
        current_item = self.prompt_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Select Prompt", "Select a prompt to edit.")
            return
        old_text = current_item.text()
        new_text, ok = QInputDialog.getText(self, "Edit Prompt", "Prompt Text:", text=old_text)
        if ok and new_text:
            index = self.data[category].index(old_text)
            self.data[category][index] = new_text
            self.refresh_prompt_list()
            self.save_data()
            self.promptsUpdated.emit(self.data)

    def remove_prompt(self):
        category = self.category_combo.currentText()
        current_item = self.prompt_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Select Prompt", "Select a prompt to remove.")
            return
        prompt_text = current_item.text()
        if QMessageBox.question(self, "Delete Prompt", f"Delete prompt:\n{prompt_text}?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.data[category].remove(prompt_text)
            self.refresh_prompt_list()
            self.save_data()
            self.promptsUpdated.emit(self.data)

    def load_data(self):
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}
        else:
            self.data = {}

    def save_data(self):
        try:
            with open(self.json_path, "w") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error Saving Data", str(e))


class SearchFieldDashboard(QMainWindow):

    def __init__(self):
        super().__init__()
        self.json_directory = "./Dashboard/json/"
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
        self.setWindowTitle("Search Field Dashboard")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        if IS_PHONE:
            self.setGeometry(50, 50, 400, 800)
        else:
            self.setGeometry(100, 100, 1400, 900)
        self.statusBar = self.statusBar()
        self.statusBar.setStyleSheet("color: #FFFFFF; background-color: #1C1C1C;")

        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(self.undo)
        self.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.triggered.connect(self.redo)
        self.addAction(redo_action)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(main_widget)
        apply_dark_theme(main_widget)

        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)

        from PySide6.QtWidgets import QTabWidget
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabBar::tab:selected { background: #2E2E2E; }
            QTabBar::tab { background: #1C1C1C; color: #FFFFFF; padding: 10px; }
            QTabWidget::pane { border: 1px solid #555555; }
        """)

        dashboard_tab = QWidget()
        dash_layout = QVBoxLayout(dashboard_tab)
        dash_layout.setContentsMargins(0, 0, 0, 0)
        dash_layout.setSpacing(10)
        search_fields_container = QWidget()
        search_fields_layout = QHBoxLayout(search_fields_container)
        search_fields_layout.setContentsMargins(0, 0, 0, 0)
        search_fields_layout.setSpacing(10)

        left_menu = QFrame()
        left_menu.setStyleSheet("""
            QFrame {
                background-color: #1C1C1C;
                border: 2px solid #333333;
                border-radius: 10px;
            }
        """)
        left_menu.setFixedWidth(250)
        left_layout = QVBoxLayout(left_menu)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)
        add_field_btn = StyledButton("➕ Add New Search Field", font_size=12)
        add_field_btn.setToolTip("Add a new search field")
        add_field_btn.clicked.connect(self.add_search_field)
        left_layout.addWidget(add_field_btn)
        load_btn = StyledButton("📂 Load from JSON", font_size=12)
        load_btn.setToolTip("Load search fields from JSON")
        load_btn.clicked.connect(lambda: self.load_data(self.json_files[self.current_file_index]))
        left_layout.addWidget(load_btn)
        add_page_btn = StyledButton("➕ Add New Page", font_size=12)
        add_page_btn.setToolTip("Add a new search fields page")
        add_page_btn.clicked.connect(self.add_page)
        left_layout.addWidget(add_page_btn)
        remove_page_btn = StyledButton("🗑️ Remove Current Page", font_size=12)
        remove_page_btn.setToolTip("Remove the current search fields page")
        remove_page_btn.clicked.connect(self.remove_current_page)
        left_layout.addWidget(remove_page_btn)
        undo_btn = StyledButton("↩️ Undo", font_size=12)
        undo_btn.setToolTip("Undo last action (Ctrl+Z)")
        undo_btn.clicked.connect(self.undo)
        left_layout.addWidget(undo_btn)
        redo_btn = StyledButton("↪️ Redo", font_size=12)
        redo_btn.setToolTip("Redo last undone action (Ctrl+Y)")
        redo_btn.clicked.connect(self.redo)
        left_layout.addWidget(redo_btn)
        navigation_label = QLabel("Navigate Pages:")
        navigation_label.setStyleSheet("color: #FFFFFF; font-size: 14px;")
        left_layout.addWidget(navigation_label)
        prev_page_btn = StyledButton("⬅️ Previous Page", "#007BFF", font_size=12)
        prev_page_btn.setToolTip("Go to the previous page")
        prev_page_btn.clicked.connect(self.prev_page)
        left_layout.addWidget(prev_page_btn)
        next_page_btn = StyledButton("➡️ Next Page", "#007BFF", font_size=12)
        next_page_btn.setToolTip("Go to the next page")
        next_page_btn.clicked.connect(self.next_page)
        left_layout.addWidget(next_page_btn)
        left_layout.addStretch()
        search_fields_layout.addWidget(left_menu)

        right_content = QWidget()
        right_layout = QVBoxLayout(right_content)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        if IS_PHONE:
            self.fields_layout = QVBoxLayout(scroll_content)
        else:
            self.fields_layout = QGridLayout(scroll_content)
            self.fields_layout.setSpacing(20)
        scroll_area.setWidget(scroll_content)
        right_layout.addWidget(scroll_area)
        search_layout = QHBoxLayout()
        self.global_search_input = QLineEdit()
        self.global_search_input.setPlaceholderText("Search across all fields..." if not IS_PHONE else "Search...")
        self.global_search_input.setToolTip("Enter a term to search across all search fields")
        self.global_search_input.returnPressed.connect(self.search_term)
        search_layout.addWidget(self.global_search_input)
        search_btn = StyledButton("🔍 Search", font_size=12)
        search_btn.setToolTip("Search across all search fields")
        search_btn.clicked.connect(self.search_term)
        search_btn.setFixedHeight(30 if not IS_PHONE else 40)
        search_layout.addWidget(search_btn)
        right_layout.addLayout(search_layout)
        search_fields_layout.addWidget(right_content)
        dash_layout.addWidget(search_fields_container)
        tabs.addTab(dashboard_tab, "Search Dashboard")

        # Toolbox Panel for internal filtering and tag filter
        toolbox_panel = QFrame()
        toolbox_panel.setStyleSheet("""
            QFrame {
                background-color: #1C1C1C;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 10px;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton {
                background-color: #B22222;
                color: #FFFFFF;
                border: 1px solid #8B0000;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #FF0000;
            }
        """)
        toolbox_layout = QHBoxLayout(toolbox_panel)
        toolbox_layout.setContentsMargins(10, 10, 10, 10)
        toolbox_layout.setSpacing(10)
        filter_label = QLabel("Filter by Tag:")
        toolbox_layout.addWidget(filter_label)
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Enter tag...")
        toolbox_layout.addWidget(self.filter_input)
        filter_btn = StyledButton("Apply Filter", font_size=12)
        filter_btn.setToolTip("Filter search fields by tag")
        filter_btn.clicked.connect(self.apply_filter)
        toolbox_layout.addWidget(filter_btn)
        clear_filter_btn = StyledButton("Clear Filter", font_size=12)
        clear_filter_btn.setToolTip("Clear active filter")
        clear_filter_btn.clicked.connect(self.clear_filter)
        toolbox_layout.addWidget(clear_filter_btn)
        dash_layout.addWidget(toolbox_panel)

        # Prompt Vault Tab
        vault_tab = QWidget()
        vault_layout = QVBoxLayout(vault_tab)
        vault_layout.setContentsMargins(0, 0, 0, 0)
        vault_layout.setSpacing(10)
        self.prompt_vault = PromptVaultWidget()
        vault_layout.addWidget(self.prompt_vault)
        tabs.addTab(vault_tab, "AI Prompt Vault")

        content_layout.addWidget(tabs)
        main_layout.addWidget(content_widget)
        self.setStyleSheet("QMainWindow { background-color: transparent; }")
        main_layout.addStretch()

    def apply_filter(self):
        tag = self.filter_input.text().strip().lower()
        if not tag:
            QMessageBox.warning(self, "Empty Filter", "Please enter a tag to filter.")
            return
        # Assume each search field has a "tags" key (even if empty)
        filtered_fields = [field for field in self.search_fields
                           if "tags" in field and any(tag == t.lower() for t in field["tags"])]
        if not filtered_fields:
            QMessageBox.information(self, "No Results", f"No search fields found with tag '{tag}'.")
        else:
            # For simplicity, replace the UI view with filtered fields.
            self.search_fields = filtered_fields
            self.refresh_ui()
            self.statusBar.showMessage(f"Filtered to fields with tag '{tag}'.", 3000)

    def clear_filter(self):
        self.filter_input.clear()
        self.load_data(self.json_files[self.current_file_index])
        self.statusBar.showMessage("Filter cleared.", 3000)

    def add_page(self):
        new_index = len(self.json_files)
        new_file = os.path.join(self.json_directory, f"search_fields_{new_index}.json")
        try:
            with open(new_file, "w") as f:
                json.dump([], f, indent=4)
            self.json_files.append(new_file)
            self.current_file_index = new_index
            self.load_data(new_file)
            self.statusBar.showMessage(f"Added and switched to new page '{new_file}'.", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add new page: {e}")

    def remove_current_page(self):
        if len(self.json_files) <= 1:
            QMessageBox.warning(self, "Cannot Remove Page", "At least one page must exist.")
            return
        current_file = self.json_files[self.current_file_index]
        reply = QMessageBox.question(self, 'Remove Page',
                                     f"Are you sure you want to remove the current page '{current_file}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                os.remove(current_file)
                self.json_files.pop(self.current_file_index)
                if self.current_file_index >= len(self.json_files):
                    self.current_file_index = len(self.json_files) - 1
                self.load_data(self.json_files[self.current_file_index])
                self.statusBar.showMessage(f"Removed page '{current_file}'.", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove page '{current_file}': {e}")

    def add_search_field(self):
        field_id = str(len(self.search_fields))
        field_name = f"Search Field {len(self.search_fields) + 1}"
        field_widget = SearchFieldWidget(field_id, field_name)
        field_widget.itemAdded.connect(self.on_item_added)
        field_widget.itemRemoved.connect(self.on_item_removed)
        field_widget.fieldRemoved.connect(self.on_field_removed)
        if IS_PHONE:
            self.fields_layout.addWidget(field_widget)
        else:
            row, col = divmod(len(self.search_fields), 2)
            self.fields_layout.addWidget(field_widget, row, col)
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
            "tags": []   # Initialize an empty tag list
        })
        self.update_history()
        self.save_data()
        self.statusBar.showMessage(f"Added '{field_name}' to '{self.json_files[self.current_file_index]}'.", 3000)

    def on_item_added(self, field_id, item):
        for field in self.search_fields:
            if field["id"] == field_id:
                field["items"].append(item)
                break
        self.update_history()
        self.save_data()
        self.statusBar.showMessage(f"Item '{item}' added.", 3000)

    def on_item_removed(self, field_id, item):
        for field in self.search_fields:
            if field["id"] == field_id:
                field["items"].remove(item)
                break
        self.update_history()
        self.save_data()
        self.statusBar.showMessage(f"Item '{item}' removed.", 3000)

    def on_field_removed(self, field_id):
        field_name = ""
        for i, field in enumerate(self.search_fields):
            if field["id"] == field_id:
                field_name = field["name"]
                del self.search_fields[i]
                break
        self.refresh_ui()
        self.update_history()
        self.save_data()
        self.statusBar.showMessage(f"Field '{field_name}' deleted from '{self.json_files[self.current_file_index]}'.", 3000)
        if not self.search_fields and len(self.json_files) > 1:
            reply = QMessageBox.question(self, 'Remove Empty Page',
                                         f"The current page '{self.json_files[self.current_file_index]}' is empty. Do you want to remove it?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.remove_current_page()

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
            self.statusBar.showMessage("Undid last action.", 3000)
        else:
            self.statusBar.showMessage("Nothing to undo.", 3000)

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.search_fields = json.loads(json.dumps(self.history[self.history_index]))
            self.refresh_ui()
            self.save_data()
            self.statusBar.showMessage("Redid action.", 3000)
        else:
            self.statusBar.showMessage("Nothing to redo.", 3000)

    def refresh_ui(self):
        for i in reversed(range(self.fields_layout.count())):
            widget = self.fields_layout.itemAt(i).widget()
            if widget:
                self.fields_layout.removeWidget(widget)
                widget.deleteLater()
        for index, field in enumerate(self.search_fields):
            field_widget = SearchFieldWidget(
                field["id"],
                field["name"],
                swap_words=field.get("swap_words", False),
                swap_sites=field.get("swap_sites", False),
                swap_words_before=field.get("swap_words_before", ""),
                swap_words_after=field.get("swap_words_after", ""),
                swap_sites_before=field.get("swap_sites_before", ""),
                swap_sites_after=field.get("swap_sites_after", "")
            )
            # Set tags for the widget for potential later use:
            field_widget.tags = field.get("tags", [])
            field_widget.itemAdded.connect(self.on_item_added)
            field_widget.itemRemoved.connect(self.on_item_removed)
            field_widget.fieldRemoved.connect(self.on_field_removed)
            for item in field["items"]:
                list_item = QListWidgetItem(item)
                list_item.setFlags(list_item.flags() | Qt.ItemIsEditable)
                field_widget.item_list.addItem(list_item)
            if IS_PHONE:
                self.fields_layout.addWidget(field_widget)
            else:
                row, col = divmod(index, 2)
                self.fields_layout.addWidget(field_widget, row, col)
        self.statusBar.showMessage("UI refreshed.", 3000)

    def save_data(self):
        file_name = self.json_files[self.current_file_index]
        try:
            with open(file_name, "w") as f:
                json.dump(self.search_fields, f, indent=4)
            self.statusBar.showMessage(f"Data saved to '{file_name}'.", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save data to '{file_name}': {e}")

    def load_data(self, file_name=None):
        if file_name is None:
            file_name = self.json_files[self.current_file_index]
        try:
            with open(file_name, "r") as f:
                self.search_fields = json.load(f)
            self.refresh_ui()
            self.update_history()
            self.statusBar.showMessage(f"Data loaded from '{file_name}'.", 5000)
        except FileNotFoundError:
            QMessageBox.warning(self, "Warning", f"No saved data found in '{file_name}'.")
            self.search_fields = []
            self.refresh_ui()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data from '{file_name}': {e}")

    def next_page(self):
        if not self.json_files:
            QMessageBox.warning(self, "No Pages", "No search field pages available.")
            return
        self.current_file_index = (self.current_file_index + 1) % len(self.json_files)
        self.load_data(self.json_files[self.current_file_index])
        self.statusBar.showMessage(f"Switched to '{self.json_files[self.current_file_index]}'.", 3000)

    def prev_page(self):
        if not self.json_files:
            QMessageBox.warning(self, "No Pages", "No search field pages available.")
            return
        self.current_file_index = (self.current_file_index - 1) % len(self.json_files)
        self.load_data(self.json_files[self.current_file_index])
        self.statusBar.showMessage(f"Switched to '{self.json_files[self.current_file_index]}'.", 3000)

    def search_term(self):
        term = self.global_search_input.text().strip()
        if not term:
            QMessageBox.warning(self, "Empty Search", "Please enter a search term.")
            return
        matching_fields = []
        for field in self.search_fields:
            for item in field["items"]:
                clean_item = item
                if item.startswith("site:"):
                    clean_item = item.replace("site:", "")
                clean_item = clean_item.replace('"', '')
                if term.lower() in clean_item.lower():
                    matching_fields.append(field["name"])
                    break
        if matching_fields:
            fields_str = "\n".join(matching_fields)
            QMessageBox.information(self, "Search Results",
                                    f"Search term '{term}' found in the following fields:\n{fields_str}")
        else:
            QMessageBox.information(self, "Search Results",
                                    f"Search term '{term}' was not found in any search field.")

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
                func_code = ast.get_source_segment(code, node)
                if func_code:
                    functions.append(func_code)
        return imports, functions

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    main_palette = QPalette()
    main_palette.setColor(QPalette.Window, QColor(20, 20, 20))
    main_palette.setColor(QPalette.WindowText, Qt.white)
    main_palette.setColor(QPalette.Base, QColor(30, 30, 30))
    main_palette.setColor(QPalette.AlternateBase, QColor(35, 35, 35))
    main_palette.setColor(QPalette.ToolTipBase, QColor(30, 30, 30))
    main_palette.setColor(QPalette.ToolTipText, Qt.white)
    main_palette.setColor(QPalette.Text, Qt.white)
    main_palette.setColor(QPalette.Button, QColor(45, 45, 45))
    main_palette.setColor(QPalette.ButtonText, Qt.white)
    main_palette.setColor(QPalette.BrightText, Qt.red)
    main_palette.setColor(QPalette.Highlight, QColor(70, 70, 70))
    main_palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(main_palette)
    dashboard = SearchFieldDashboard()
    dashboard.show()
    sys.exit(app.exec())
