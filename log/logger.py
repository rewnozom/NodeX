#!/usr/bin/env python3
# ./log/logger.py

import inspect
import logging
import os
import re
import sys
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener
from queue import Queue
from typing import Literal, Mapping, List, Any, Optional

_logged_qt_messages = set()

# Import configurations
from Config.AppConfig.config import (
    DEBUG_MODE,
    LOG_DIR,
    MAX_LOG_FILE_SIZE,
    BACKUP_COUNT,
    SENSITIVE_PATTERNS,
    LOG_COLORS,
    LOG_TIMESTAMP_FORMAT,
    LOG_FILENAME_TEMPLATE,
    FILE_ENCODING,
)

from .message_collector import MessageCollector

# Type definitions
ColorType = Literal[
    'red', 'green', 'yellow', 'blue', 'magenta', 'cyan',
    'light_grey', 'dark_grey', 'light_red', 'light_green',
    'light_yellow', 'light_blue', 'light_magenta', 'light_cyan', 'white',
]

# Constants
RESET_CODE = "\033[0m"
DISABLE_COLOR_PRINTING = False

# ------------------- Formatters ------------------- #
class ColoredFormatter(logging.Formatter):
    """Adds colors to log messages based on log level."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with appropriate colors."""
        level_name = record.levelname
        if level_name in LOG_COLORS and not DISABLE_COLOR_PRINTING:
            color_code = f"\033[{LOG_COLORS.get(level_name, '0')}m"
            formatted_message = (
                f"{color_code}{self.formatTime(record, self.datefmt)} - "
                f"{record.name}:{level_name} - {record.filename}:{record.lineno} - "
                f"{record.getMessage()}{RESET_CODE}"
            )
            return formatted_message
        return super().format(record)

# Standard formatter for file logs
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s:%(levelname)s: %(filename)s:%(lineno)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

# ------------------- Filters ------------------- #
class SensitiveDataFilter(logging.Filter):
    """Filters out sensitive information from logs."""

    def __init__(self):
        super().__init__()
        self.patterns = self._compile_patterns(SENSITIVE_PATTERNS)

    @staticmethod
    def _compile_patterns(patterns: List[str]) -> List[re.Pattern]:
        """Compile regex patterns for sensitive data matching."""
        return [
            re.compile(
                rf"({re.escape(pattern)})\s*=\s*('|\")?(.*?)('|\")?(\s|,|$)",
                re.IGNORECASE
            )
            for pattern in patterns
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter sensitive data from log records."""
        msg = record.getMessage()
        for pattern in self.patterns:
            msg = pattern.sub(r"\1=******\5", msg)
        record.msg = msg
        return True

# ------------------- Handlers ------------------- #
def get_console_handler() -> logging.Handler:
    """Create and configure console handler."""
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s:%(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    return console_handler

def get_file_handler() -> logging.Handler:
    """Create and configure file handler."""
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime(LOG_TIMESTAMP_FORMAT)
    file_name = LOG_FILENAME_TEMPLATE.format(timestamp=timestamp)
    file_path = os.path.join(LOG_DIR, file_name)
    
    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=MAX_LOG_FILE_SIZE,
        backupCount=BACKUP_COUNT,
        encoding=FILE_ENCODING
    )
    file_handler.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
    file_handler.setFormatter(file_formatter)
    return file_handler

# ------------------- Logger Setup ------------------- #
# Initialize the central logger
try:
    logger = logging.getLogger('app_logger')
    logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)

    if not logger.handlers:
        # Create logging queue for async logging
        log_queue = Queue(-1)
        
        # Create and configure handlers
        console_handler = get_console_handler()
        file_handler = get_file_handler()
        queue_handler = QueueHandler(log_queue)
        
        # Add queue handler to logger
        logger.addHandler(queue_handler)
        
        # Add sensitive data filter
        logger.addFilter(SensitiveDataFilter())
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        # Configure and start queue listener
        listener = QueueListener(
            log_queue,
            console_handler,
            file_handler,
            respect_handler_level=True
        )
        listener.start()
        
        # Log initialization
        logger.debug('Logging initialized')
        logger.debug(f'Logging to {os.path.join(LOG_DIR, "log.log")}')
except Exception as e:
    print(f"Critical error during logger initialization: {e}")
    fallback_logger = logging.getLogger('fallback_logger')
    fallback_handler = logging.StreamHandler()
    fallback_logger.addHandler(fallback_handler)
    logger = fallback_logger
    logger.error("Falling back to basic logging configuration")

# Initialize MessageCollector
message_collector = MessageCollector(logger.info)

# ------------------- Error Handling ------------------- #
def log_uncaught_exceptions(ex_cls: type, ex: Exception, tb: Any) -> None:
    """Handle uncaught exceptions by logging them."""
    logger.error('Uncaught exception', exc_info=(ex_cls, ex, tb))

sys.excepthook = log_uncaught_exceptions

# ------------------- Qt Integration ------------------- #
def qt_message_handler(mode: int, context: Any, message: str) -> None:
    """Handle Qt messages by redirecting them to the logger."""
    # Kolla om meddelandet redan har loggats
    if message in _logged_qt_messages:
        return
    
    # Lägg till meddelandet i vår set av loggade meddelanden
    _logged_qt_messages.add(message)
    
    handlers = {
        logging.DEBUG: lambda m: logger.debug(f"QtDebug: {m}"),
        logging.INFO: lambda m: logger.info(f"QtInfo: {m}"),
        logging.WARNING: lambda m: logger.warning(f"QtWarning: {m}"),
        logging.ERROR: lambda m: logger.error(f"QtError: {m}"),
        logging.CRITICAL: lambda m: logger.critical(f"QtCritical: {m}")
    }
    handler = handlers.get(mode, lambda m: logger.info(f"Qt: {m}"))
    handler(message)

# ------------------- Debug Tools ------------------- #
# IceCream integration for debugging
try:
    from icecream import ic as original_ic
    ICECREAM_AVAILABLE = True
except ImportError:
    ICECREAM_AVAILABLE = False
    original_ic = lambda *args, **kwargs: None

if ICECREAM_AVAILABLE and DEBUG_MODE:
    def ic(*args: Any) -> None:
        """Enhanced debug printing using IceCream."""
        frame = inspect.currentframe().f_back
        if frame is not None:
            info = inspect.getframeinfo(frame)
            expression = ", ".join(str(arg) for arg in args)
            logger.debug(f"ic| {info.filename}:{info.lineno} - {expression}")
else:
    ic = lambda *args, **kwargs: None

# ------------------- Logger Manager ------------------- #
class LoggerManager:
    """Manages logging setup and ensures single logger instance."""
    
    _instance: Optional['LoggerManager'] = None
    _lock = threading.Lock()

    def __new__(cls, config_manager=None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LoggerManager, cls).__new__(cls)
                cls._instance._initialize(config_manager)
            return cls._instance

    def _initialize(self, config_manager):
        """Initialize logger manager instance."""
        self.config_manager = config_manager
        self.message_collector = MessageCollector()
        self.logger = logger  # Use the global logger

    def batch_log(self, message_type: str, content: str, level: str = 'INFO') -> None:
        """Add message to batch collector."""
        self.message_collector.add_message(message_type, content, level)
    
    def flush_logs(self) -> None:
        """Flush collected messages."""
        self.message_collector.flush()
    
    def close(self) -> None:
        """Clean shutdown of logging system."""
        self.flush_logs()
        self.close_handlers()

    def get_logger(self) -> logging.Logger:
        """Get the current logger instance."""
        return self.logger

    def update_log_level(self) -> None:
        """Update logging level from configuration."""
        log_level_str = (
            self.config_manager.get_config_value("logging_level", "DEBUG").upper()
            if self.config_manager
            else "DEBUG"
        )
        log_level = getattr(logging, log_level_str, logging.DEBUG)
        self.logger.setLevel(log_level)
        for handler in self.logger.handlers:
            handler.setLevel(log_level)
        self.logger.debug(f"Updated logger level to {log_level_str}")

    def close_handlers(self) -> None:
        """Close all handlers and release resources."""
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)
        self.logger.debug("Closed all logger handlers.")

# ------------------- Exports ------------------- #
__all__ = [
    'logger',
    'LoggerManager',
    'SensitiveDataFilter',
    'ColoredFormatter',
    'qt_message_handler',
    'get_console_handler',
    'get_file_handler',
    'log_uncaught_exceptions',
    'RESET_CODE',
    'ICECREAM_AVAILABLE',
    'log_queue',
    'listener',
    'console_handler',
    'file_handler',
    'queue_handler',
    'file_formatter',
    'ic',
    'ColorType',
]