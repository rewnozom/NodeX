#!/usr/bin/env python3
# ./log/__init__.py

"""
Logging package initialization.
Exports the logging interface and related utilities.
"""

from .logger import (
    # Core logging components
    logger,
    LoggerManager,
    
    # Formatters and Filters
    SensitiveDataFilter,
    ColoredFormatter,
    
    # Handlers and utilities
    qt_message_handler,
    get_console_handler,
    get_file_handler,
    log_uncaught_exceptions,
    
    # Color and formatting utilities
    RESET_CODE,
    LOG_COLORS,
    DISABLE_COLOR_PRINTING,
    
    # Queue-related components
    log_queue,
    listener,
    
    # Handlers
    console_handler,
    file_handler,
    queue_handler,
    file_formatter,
    
    # Debug utilities
    ic,
    ICECREAM_AVAILABLE,
)

from .message_collector import (
    MessageCollector,
    message_collector
)

# Define package exports
__all__ = [
    # Core logging components
    "logger",
    "LoggerManager",
    
    # Formatters and Filters
    "SensitiveDataFilter",
    "ColoredFormatter",
    
    # Handlers and utilities
    "qt_message_handler",
    "get_console_handler",
    "get_file_handler",
    "log_uncaught_exceptions",
    
    # Color and formatting utilities
    "RESET_CODE",
    "LOG_COLORS",
    "DISABLE_COLOR_PRINTING",
    
    # Queue-related components
    "log_queue",
    "listener",
    
    # Handlers
    "console_handler",
    "file_handler",
    "queue_handler",
    "file_formatter",
    
    # Debug utilities
    "ic",
    "ICECREAM_AVAILABLE",
    
    # Message collection utilities
    "MessageCollector",
    "message_collector",
]