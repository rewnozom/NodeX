# ./ai_vault_tab.py

import os
import sys
import json
import ast

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QMessageBox, QComboBox,
    QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QInputDialog
)
from frontend.Pages.desktop.Layout.Dashboard.utils.card_utils import create_card
from frontend.Pages.desktop.Layout.Dashboard.utils.theme_utils import apply_dark_theme
from frontend.Pages.desktop.Layout.Dashboard.search_tab import StyledButton  # reuse the same StyledButton

class PromptVaultWidget(QWidget):
    """
    A widget for managing an AI prompt vault with categorized prompts.
    """
    def __init__(self, json_path="./prompt_vault.json", parent=None):
        super().__init__(parent)
        self.json_path = json_path
        self.data = {}  # Structure: {category: [prompt, ...], "tags": {category: [tag, ...]}}
        self.load_data()
        self.initUI()
    
    def initUI(self):
        main_layout = QVBoxLayout(self)
        apply_dark_theme(self)
        header_label = QLabel("AI Prompt Vault")
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_label.setStyleSheet("color: #FFFFFF; background: transparent;")
        main_layout.addWidget(header_label)
        
        # Categories card
        category_card = create_card("Categories")
        cat_layout = category_card.layout()
        self.category_combo = QComboBox()
        self.category_combo.currentIndexChanged.connect(self.refresh_prompt_list)
        cat_layout.addWidget(self.category_combo)
        add_cat_btn = StyledButton("➕", font_size=12)
        add_cat_btn.setToolTip("Add category")
        add_cat_btn.clicked.connect(self.add_category)
        cat_layout.addWidget(add_cat_btn)
        edit_cat_btn = StyledButton("✎", font_size=12)
        edit_cat_btn.setToolTip("Edit category")
        edit_cat_btn.clicked.connect(self.edit_category)
        cat_layout.addWidget(edit_cat_btn)
        del_cat_btn = StyledButton("🗑️", font_size=12)
        del_cat_btn.setToolTip("Delete category")
        del_cat_btn.clicked.connect(self.delete_category)
        cat_layout.addWidget(del_cat_btn)
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
        
        # Toolbox panel for filtering by tag (for vault entries)
        toolbox_panel = QWidget()
        toolbox_layout = QHBoxLayout(toolbox_panel)
        tag_filter_label = QLabel("Filter by Tag:")
        toolbox_layout.addWidget(tag_filter_label)
        self.vault_filter_input = QLineEdit()
        self.vault_filter_input.setPlaceholderText("Enter tag...")
        toolbox_layout.addWidget(self.vault_filter_input)
        filter_btn = StyledButton("Apply Filter", font_size=12)
        filter_btn.clicked.connect(self.apply_filter)
        toolbox_layout.addWidget(filter_btn)
        clear_filter_btn = StyledButton("Clear Filter", font_size=12)
        clear_filter_btn.clicked.connect(self.clear_filter)
        toolbox_layout.addWidget(clear_filter_btn)
        main_layout.addWidget(toolbox_panel)
        
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
            self.category_combo.setCurrentText(current)
        self.refresh_prompt_list()
    
    def refresh_prompt_list(self):
        self.prompt_list.clear()
        category = self.category_combo.currentText()
        if category and category in self.data:
            for prompt in self.data[category]:
                li = QListWidgetItem(prompt)
                li.setFlags(li.flags() | Qt.ItemIsEditable)
                self.prompt_list.addItem(li)
    
    def add_category(self):
        text, ok = QInputDialog.getText(self, "Add Category", "Category Name:")
        if ok and text:
            if text in self.data:
                QMessageBox.warning(self, "Duplicate", f"Category '{text}' exists.")
                return
            self.data[text] = []
            self.refresh_category_combo()
            self.save_data()
    
    def edit_category(self):
        current = self.category_combo.currentText()
        if not current:
            return
        new_text, ok = QInputDialog.getText(self, "Edit Category", "New Category Name:", text=current)
        if ok and new_text and new_text != current:
            if new_text in self.data:
                QMessageBox.warning(self, "Duplicate", f"Category '{new_text}' exists.")
                return
            self.data[new_text] = self.data.pop(current)
            self.refresh_category_combo()
            self.save_data()
    
    def delete_category(self):
        current = self.category_combo.currentText()
        if not current:
            return
        reply = QMessageBox.question(self, "Delete Category", f"Delete category '{current}'?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.data[current]
            self.refresh_category_combo()
            self.save_data()
    
    def add_prompt(self):
        category = self.category_combo.currentText()
        prompt_text = self.prompt_input.text().strip()
        if not prompt_text:
            QMessageBox.warning(self, "Empty Prompt", "Enter prompt text.")
            return
        self.data[category].append(prompt_text)
        self.prompt_input.clear()
        self.refresh_prompt_list()
        self.save_data()
    
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
    
    def remove_prompt(self):
        category = self.category_combo.currentText()
        current_item = self.prompt_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Select Prompt", "Select a prompt to remove.")
            return
        prompt_text = current_item.text()
        reply = QMessageBox.question(self, "Delete Prompt", f"Delete prompt:\n{prompt_text}?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.data[category].remove(prompt_text)
            self.refresh_prompt_list()
            self.save_data()
    
    def apply_filter(self):
        tag = self.vault_filter_input.text().strip().lower()
        if not tag:
            QMessageBox.warning(self, "Empty Filter", "Enter a tag to filter.")
            return
        # For illustration, assume we have stored tags per category (this can be extended)
        filtered = {}
        for cat, prompts in self.data.items():
            # For each category, if the category name contains the tag (or you could store separate tags)
            if tag in cat.lower():
                filtered[cat] = prompts
        if not filtered:
            QMessageBox.information(self, "No Results", f"No categories found with tag '{tag}'.")
        else:
            self.data = filtered
            self.refresh_category_combo()
    
    def clear_filter(self):
        self.vault_filter_input.clear()
        self.load_data(self.json_path)
    
    def load_data(self, file_name=None):
        if file_name is None:
            file_name = self.json_path
        try:
            with open(file_name, "r") as f:
                self.data = json.load(f)
        except Exception:
            self.data = {}
    
    def save_data(self):
        try:
            with open(self.json_path, "w") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error Saving Data", str(e))

class AIVaultTab(QWidget):
    """
    Wrapper for the AI Prompt Vault tab.
    """
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.vault_widget = PromptVaultWidget()
        layout.addWidget(self.vault_widget)
