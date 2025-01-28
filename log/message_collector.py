# ./shared/log/message_collector.py

import threading
from collections import defaultdict
from typing import Callable, Optional

class MessageCollector:
    """Collects and groups similar log messages for batch processing."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, log_function: Optional[Callable] = None):
        if not getattr(self, '_initialized', False):
            self._messages = defaultdict(list)
            self._lock = threading.Lock()
            self._flush_threshold = 100  # Auto-flush after this many messages
            self.log_function = log_function or print  # Use print if no logger provided
            self._initialized = True

    def add_message(self, message_type: str, content: str, level: str = 'INFO'):
        """Add a message to be collected."""
        with self._lock:
            self._messages[message_type].append({
                'content': content,
                'level': level
            })

            # Auto-flush if threshold reached
            if sum(len(msgs) for msgs in self._messages.values()) >= self._flush_threshold:
                self.flush()

    def flush(self):
        """Flush collected messages and log them as groups."""
        with self._lock:
            for message_type, messages in self._messages.items():
                if not messages:
                    continue

                if message_type == "discovered_page":
                    # Group all discovered pages into one message
                    pages = ", ".join(f"'{msg['content']}'" for msg in messages)
                    self.log_function(f"INFO: Discovered pages: {pages}")

                elif message_type == "error_discovering_page":
                    # Group errors by their error message
                    error_groups = defaultdict(list)
                    for msg in messages:
                        if isinstance(msg['content'], tuple):
                            page_name, error_msg = msg['content']
                            error_groups[error_msg].append(page_name)

                    for error_msg, pages in error_groups.items():
                        page_list = ", ".join(f"'{page}'" for page in pages)
                        self.log_function(f"ERROR: Error discovering pages [{page_list}]: {error_msg}")

                else:
                    # Handle generic grouped messages
                    grouped_by_level = defaultdict(list)
                    for msg in messages:
                        grouped_by_level[msg['level']].append(msg['content'])

                    for level, contents in grouped_by_level.items():
                        for content in contents:
                            self.log_function(f"{level}: {message_type.upper()} - {content}")

            self._messages.clear()

# Expose the message_collector instance for general use
message_collector = MessageCollector()
