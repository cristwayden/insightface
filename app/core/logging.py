"""
app/core/logging.py
System-wide logging configuration.
Automatically logs to console (with colors) and to a file (with rotation).
"""
import logging
import os
from logging.handlers import RotatingFileHandler

from app.core.config import settings

# Ensure the logs directory exists
os.makedirs(settings.LOG_DIR, exist_ok=True)
_log_file_path = os.path.join(settings.LOG_DIR, settings.LOG_FILE)


class ColoredFormatter(logging.Formatter):
    """Custom colors for console output."""

    COLORS = {
        "DEBUG": "\033[94m",     # Blue
        "INFO": "\033[92m",      # Green
        "WARNING": "\033[93m",   # Yellow
        "ERROR": "\033[91m",     # Red
        "CRITICAL": "\033[91m",  # Red
        "RESET": "\033[0m",
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        record.levelname = f"{color}{record.levelname:8}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logger() -> logging.Logger:
    """Initialize and configure the root logger."""
    logger = logging.getLogger("InsightFace")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Clear old handlers (if called multiple times)
    if logger.handlers:
        logger.handlers.clear()

    # Formats
    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_format = ColoredFormatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1. Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(console_format)
    logger.addHandler(ch)

    # 2. File handler (Rotating)
    fh = RotatingFileHandler(
        _log_file_path,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(file_format)
    logger.addHandler(fh)

    return logger


# Initialize shared logger
main_logger = setup_logger()


def get_logger(name: str) -> logging.Logger:
    """Get a child logger by module name (e.g.: get_logger(__name__))."""
    return main_logger.getChild(name.split(".")[-1])


def get_log_file_path() -> str:
    """Return the absolute path of the current log file."""
    return os.path.abspath(_log_file_path)
