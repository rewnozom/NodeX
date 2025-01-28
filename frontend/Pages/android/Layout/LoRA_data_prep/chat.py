
import sys
import os
import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QLabel, QComboBox, QListWidget, QListWidgetItem, QSpinBox, QDoubleSpinBox, QGridLayout, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, QEvent
from models import MODELS, get_model
from config import Config

CHAT_HISTORY_DIR = "./chat_history"
if not os.path.exists(CHAT_HISTORY_DIR):
    os.makedirs(CHAT_HISTORY_DIR)

class RenameChatDialog(QDialog):
    def __init__(self, current_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ändra namn")
        self.current_name = current_name
        self.new_name = None

        layout = QVBoxLayout(self)
        self.name_edit = QLineEdit(self)
        self.name_edit.setText(current_name)
        layout.addWidget(QLabel("Nytt namn:"))
        layout.addWidget(self.name_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        self.new_name = self.name_edit.text()
        super().accept()

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Chat GUI")
        self.config = Config()
        self.current_chat = []  # List to hold current chat messages
        self.current_chat_name = "Ny Chat"
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget(self)
        main_layout = QHBoxLayout(main_widget)

        # Left panel: Chat History
        self.history_list = QListWidget(self)
        self.history_list.itemClicked.connect(self.load_history)
        main_layout.addWidget(self.history_list, 1)

        # Right panel: Chat & Settings
        right_panel = QWidget(self)
        right_layout = QVBoxLayout(right_panel)

        # Top: Buttons for chat management
        buttons_layout = QHBoxLayout()
        self.new_chat_btn = QPushButton("Ny Chat", self)
        self.new_chat_btn.clicked.connect(self.new_chat)
        buttons_layout.addWidget(self.new_chat_btn)

        self.remove_chat_btn = QPushButton("Ta Bort Chat", self)
        self.remove_chat_btn.clicked.connect(self.remove_chat)
        buttons_layout.addWidget(self.remove_chat_btn)

        self.rename_chat_btn = QPushButton("Ändra Namn", self)
        self.rename_chat_btn.clicked.connect(self.rename_chat)
        buttons_layout.addWidget(self.rename_chat_btn)
        right_layout.addLayout(buttons_layout)

        # Middle: Chat display and input
        self.chat_display = QTextEdit(self)
        self.chat_display.setReadOnly(True)
        right_layout.addWidget(self.chat_display, 3)

        self.chat_input = QTextEdit(self)
        self.chat_input.installEventFilter(self)
        right_layout.addWidget(self.chat_input, 1)

        # Bottom: AI modell och inställningar
        settings_layout = QGridLayout()
        # Modell
        settings_layout.addWidget(QLabel("Modell:"), 0, 0)
        self.model_combo = QComboBox(self)
        self.populate_models()
        settings_layout.addWidget(self.model_combo, 0, 1)

        # Temperature
        settings_layout.addWidget(QLabel("Temperature:"), 1, 0)
        self.temperature_spin = QDoubleSpinBox(self)
        self.temperature_spin.setRange(0.0, 1.0)
        self.temperature_spin.setSingleStep(0.05)
        self.temperature_spin.setValue(self.config.CHAT_TEMPERATURE)
        settings_layout.addWidget(self.temperature_spin, 1, 1)

        # Max tokens
        settings_layout.addWidget(QLabel("Max Tokens:"), 2, 0)
        self.max_tokens_spin = QSpinBox(self)
        self.max_tokens_spin.setRange(1, 2048)
        self.max_tokens_spin.setValue(256)
        settings_layout.addWidget(self.max_tokens_spin, 2, 1)

        # Top P sampling
        settings_layout.addWidget(QLabel("Top P:"), 3, 0)
        self.top_p_spin = QDoubleSpinBox(self)
        self.top_p_spin.setRange(0.0, 1.0)
        self.top_p_spin.setSingleStep(0.05)
        self.top_p_spin.setValue(1.0)
        settings_layout.addWidget(self.top_p_spin, 3, 1)

        # Min P sampling
        settings_layout.addWidget(QLabel("Min P:"), 4, 0)
        self.min_p_spin = QDoubleSpinBox(self)
        self.min_p_spin.setRange(0.0, 1.0)
        self.min_p_spin.setSingleStep(0.05)
        self.min_p_spin.setValue(0.0)
        settings_layout.addWidget(self.min_p_spin, 4, 1)

        # System prompt
        settings_layout.addWidget(QLabel("Systemprompt:"), 5, 0)
        self.system_prompt_edit = QLineEdit(self)
        settings_layout.addWidget(self.system_prompt_edit, 5, 1)

        right_layout.addLayout(settings_layout)

        # Send Button
        self.send_btn = QPushButton("Skicka Meddelande", self)
        self.send_btn.clicked.connect(self.send_message)
        right_layout.addWidget(self.send_btn)

        main_layout.addWidget(right_panel, 3)
        self.setCentralWidget(main_widget)
        self.load_chat_history_list()

    def populate_models(self):
        # Populate combobox with models from MODELS dictionary
        self.model_combo.clear()
        for company in MODELS:
            for model_key in MODELS[company]:
                self.model_combo.addItem(f"{company} - {model_key}", model_key)

    def eventFilter(self, source, event):
        # Detect key press in chat input
        if source == self.chat_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and not (event.modifiers() & Qt.ShiftModifier):
                self.send_message()
                return True
        return super().eventFilter(source, event)

    def send_message(self):
        message = self.chat_input.toPlainText().strip()
        if message:
            self.append_chat("User", message)
            # Clear input field
            self.chat_input.clear()
            # Here we would send the message to the selected model
            model_key = self.model_combo.currentData()
            temperature = self.temperature_spin.value()
            # Additional parameters can be passed (max_tokens, top_p, min_p, system prompt)
            try:
                ai_model = get_model(model_key, temperature=temperature)
                # Simulate AI response for demonstration purposes
                response = f"AI Response to: {message}"
            except Exception as e:
                response = f"Error: {str(e)}"
            self.append_chat("AI", response)
            self.save_current_chat()
    
    def append_chat(self, sender, message):
        self.current_chat.append((sender, message))
        self.chat_display.append(f"<b>{sender}:</b> {message}\n")

    def new_chat(self):
        # Save current chat before starting new one
        self.save_current_chat()
        self.current_chat = []
        self.chat_display.clear()
        self.current_chat_name = "Ny Chat"

    def remove_chat(self):
        # Remove selected chat history file
        selected_item = self.history_list.currentItem()
        if selected_item:
            file_path = os.path.join(CHAT_HISTORY_DIR, selected_item.text() + ".md")
            if os.path.exists(file_path):
                os.remove(file_path)
            self.load_chat_history_list()
    
    def rename_chat(self):
        # Rename current chat
        dlg = RenameChatDialog(self.current_chat_name, self)
        if dlg.exec():
            new_name = dlg.new_name.strip()
            if new_name:
                # Rename history file if exists
                old_file = os.path.join(CHAT_HISTORY_DIR, self.current_chat_name + ".md")
                new_file = os.path.join(CHAT_HISTORY_DIR, new_name + ".md")
                if os.path.exists(old_file):
                    os.rename(old_file, new_file)
                self.current_chat_name = new_name
                self.load_chat_history_list()

    def save_current_chat(self):
        if not self.current_chat:
            return
        # Save current chat to markdown file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.current_chat_name}_{timestamp}.md"
        file_path = os.path.join(CHAT_HISTORY_DIR, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            for sender, message in self.current_chat:
                f.write(f"**{sender}:** {message}\n\n")
        self.load_chat_history_list()

    def load_chat_history_list(self):
        self.history_list.clear()
        for file in os.listdir(CHAT_HISTORY_DIR):
            if file.endswith(".md"):
                item = QListWidgetItem(file[:-3])
                self.history_list.addItem(item)

    def load_history(self, item):
        # Load selected chat history into chat display
        file_name = item.text() + ".md"
        file_path = os.path.join(CHAT_HISTORY_DIR, file_name)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.chat_display.setPlainText(content)
            # Optionally, parse the file to populate self.current_chat
            self.current_chat = []
            for line in content.splitlines():
                if line.startswith("**") and ":**" in line:
                    try:
                        sender, message = line.split(":**", 1)
                        sender = sender.replace("**", "").strip()
                        message = message.strip()
                        self.current_chat.append((sender, message))
                    except Exception:
                        continue

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
