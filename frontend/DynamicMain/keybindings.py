# ..\dynamic_main\keybindings.py
# dynamic_main/keybindings.py

from PySide6.QtGui import QShortcut, QKeySequence
from Utils.keybindnings.keybindnings import (
    Keybind_Ctrl_1, Keybind_Ctrl_2, Keybind_Ctrl_3, Keybind_Ctrl_4,
    Keybind_Ctrl_5, Keybind_Ctrl_6, Keybind_Ctrl_7, Keybind_Ctrl_8,
    Keybind_Ctrl_9, Keybind_Alt_1, Keybind_Alt_2, Keybind_Alt_3,
    Keybind_Alt_4, Keybind_Alt_5, Keybind_Alt_6, Keybind_Alt_a,
    Keybind_Shift_Enter, Keybind_Ctrl_N, Keybind_Alt_S, Keybind_Alt_C
)
from log.logger import logger

class KeyBindings:
    """Initializes and manages key bindings."""

    def __init__(self, main_window):
        self.main_window = main_window

    def init_keybindings(self):
        logger.info("Initializing key bindings...")
        
        binding_errors = []

        try:
            # Initialize Ctrl + 1-9 bindings
            for i in range(1, 10):
                try:
                    shortcut = QShortcut(QKeySequence(f"Ctrl+{i}"), self.main_window)
                    func = globals()[f"Keybind_Ctrl_{i}"]
                    shortcut.activated.connect(lambda f=func: f(self.main_window))
                except Exception as e:
                    binding_errors.append(f"Failed to bind Ctrl+{i}: {str(e)}")

            # Initialize Alt + 1-6 bindings
            for i in range(1, 7):
                try:
                    shortcut = QShortcut(QKeySequence(f"Alt+{i}"), self.main_window)
                    func = globals()[f"Keybind_Alt_{i}"]
                    shortcut.activated.connect(lambda f=func: f(self.main_window.get_current_chat_page()))
                except Exception as e:
                    binding_errors.append(f"Failed to bind Alt+{i}: {str(e)}")

            # Other keybindings
            other_bindings = [
                ("Alt+A", lambda: Keybind_Alt_a(self.main_window.get_current_chat_page())),
                ("Ctrl+N", lambda: Keybind_Ctrl_N(self.main_window)),
                ("Alt+S", lambda: Keybind_Alt_S(self.main_window)),
                ("Alt+C", lambda: Keybind_Alt_C(self.main_window.get_current_chat_page()))
            ]

            for key_sequence, callback in other_bindings:
                try:
                    shortcut = QShortcut(QKeySequence(key_sequence), self.main_window)
                    shortcut.activated.connect(callback)
                except Exception as e:
                    binding_errors.append(f"Failed to bind {key_sequence}: {str(e)}")

            if binding_errors:
                # Log only the errors that occurred
                for error in binding_errors:
                    logger.error(error)
                logger.error("Some key bindings failed to initialize")
            else:
                # Log success only once if all bindings were successful
                logger.info("Key bindings successfully setup")

        except Exception as e:
            logger.error(f"Critical error during key binding initialization: {str(e)}")
