#!/usr/bin/env python3
# ./frontend/DynamicMain/page_state_handler.py

import os
import json
from typing import Dict, Any, Optional
from log.logger import logger

class PageStateHandler:
    """
    Handles saving and loading of page state information using JSON storage.
    """
    
    DEFAULT_STATE_FILE = "./frontend/DynamicMain/last_page_state.json"
    DEFAULT_STATE = {
        "last_page": "",
        "window_state": {
            "size": {"width": 600, "height": 400},
            "position": {"x": 100, "y": 100}
        },
        "ui_state": {
            "theme": "dark",
            "sidebar_expanded": True
        }
    }

    def __init__(self, state_file: str = DEFAULT_STATE_FILE):
        """Initialize the state handler with specified state file path."""
        self.state_file = state_file
        self._ensure_state_file_exists()

    def _ensure_state_file_exists(self) -> None:
        """Ensure the state file exists, create with defaults if it doesn't."""
        try:
            if not os.path.exists(self.state_file):
                os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
                self.save_state(self.DEFAULT_STATE)
        except Exception as e:
            logger.error(f"Error ensuring state file exists: {e}")
            raise StateFileError(f"Failed to initialize state file: {str(e)}")

    def load_state(self) -> Dict[str, Any]:
        """Load the current state from JSON file."""
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("State file not found, creating new one with defaults")
            self.save_state(self.DEFAULT_STATE)
            return self.DEFAULT_STATE
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding state file: {e}")
            self.save_state(self.DEFAULT_STATE)
            return self.DEFAULT_STATE
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            raise StateLoadError(f"Failed to load state: {str(e)}")

    def save_state(self, state: Dict[str, Any]) -> None:
        """Save the current state to JSON file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving state: {e}")
            raise StateSaveError(f"Failed to save state: {str(e)}")

    def get_last_page(self) -> str:
        """Get the name of the last visited page."""
        try:
            state = self.load_state()
            return state.get("last_page", "")
        except Exception as e:
            logger.error(f"Error getting last page: {e}")
            return ""

    def save_last_page(self, page_name: str) -> None:
        """Save the name of the last visited page."""
        try:
            state = self.load_state()
            state["last_page"] = page_name
            self.save_state(state)
        except Exception as e:
            logger.error(f"Error saving last page: {e}")
            raise StateSaveError(f"Failed to save last page: {str(e)}")

    def update_window_state(self, size: Dict[str, int], position: Dict[str, int]) -> None:
        """Update window size and position state."""
        try:
            state = self.load_state()
            state["window_state"]["size"] = size
            state["window_state"]["position"] = position
            self.save_state(state)
        except Exception as e:
            logger.error(f"Error updating window state: {e}")
            raise StateSaveError(f"Failed to update window state: {str(e)}")

    def update_ui_state(self, theme: str, sidebar_expanded: bool) -> None:
        """Update UI state including theme and sidebar state."""
        try:
            state = self.load_state()
            state["ui_state"]["theme"] = theme
            state["ui_state"]["sidebar_expanded"] = sidebar_expanded
            self.save_state(state)
        except Exception as e:
            logger.error(f"Error updating UI state: {e}")
            raise StateSaveError(f"Failed to update UI state: {str(e)}")


class StateFileError(Exception):
    """Raised when there are issues with the state file."""
    pass


class StateLoadError(Exception):
    """Raised when state loading fails."""
    pass


class StateSaveError(Exception):
    """Raised when state saving fails."""
    pass