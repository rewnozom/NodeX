"""
ai_agent/utils/logging.py - Enhanced logging system
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[41m', # Red background
        'RESET': '\033[0m'      # Reset
    }

    def format(self, record):
        if hasattr(record, 'color') and not record.color:
            return super().format(record)
            
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.msg = f"{color}{record.msg}{self.COLORS['RESET']}"
        return super().format(record)

class Logger:
    """Enhanced logger with file and console output"""
    
    def __init__(self, name: str, log_dir: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler with color formatting
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        console.setFormatter(CustomFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console)

        # File handler
        if log_dir:
            log_path = Path(log_dir) / f"{name}_{datetime.now():%Y%m%d}.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(file_handler)

    def debug(self, msg: str, color: bool = True):
        self.logger.debug(msg, extra={'color': color})

    def info(self, msg: str, color: bool = True):
        self.logger.info(msg, extra={'color': color})

    def warning(self, msg: str, color: bool = True):
        self.logger.warning(msg, extra={'color': color})

    def error(self, msg: str, color: bool = True):
        self.logger.error(msg, extra={'color': color})

    def critical(self, msg: str, color: bool = True):
        self.logger.critical(msg, extra={'color': color})

class AsyncLogger(Logger):
    """Logger with async support"""
    
    async def alog(self, level: str, msg: str, color: bool = True):
        getattr(self.logger, level.lower())(msg, extra={'color': color})

    async def adebug(self, msg: str, color: bool = True):
        await self.alog('DEBUG', msg, color)

    async def ainfo(self, msg: str, color: bool = True):
        await self.alog('INFO', msg, color)

    async def awarning(self, msg: str, color: bool = True):
        await self.alog('WARNING', msg, color)

    async def aerror(self, msg: str, color: bool = True):
        await self.alog('ERROR', msg, color)

    async def acritical(self, msg: str, color: bool = True):
        await self.alog('CRITICAL', msg, color)