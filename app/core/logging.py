"""
app/core/logging.py
Cấu hình hệ thống logging tập trung: RotatingFileHandler + StreamHandler.
Các module khác gọi get_logger(__name__) để lấy logger.
"""
import logging
import logging.handlers
import os

from app.core.config import settings

# ============================================================
# Setup logging một lần khi module được import lần đầu
# ============================================================

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _setup_root_logger() -> None:
    """Khởi tạo root logger với File + Console handler."""
    global _configured
    if _configured:
        return

    # Tạo thư mục logs nếu chưa có
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    log_path = os.path.join(settings.LOG_DIR, settings.LOG_FILE)

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # --- File Handler (rotating) ---
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # --- Console Handler ---
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # --- Root Logger ---
    root = logging.getLogger("InsightFace")
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.DEBUG))
    root.addHandler(file_handler)
    root.addHandler(console_handler)
    root.propagate = False

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Trả về logger con của 'InsightFace'.
    Gọi: logger = get_logger(__name__)
    """
    _setup_root_logger()
    return logging.getLogger(f"InsightFace.{name}")


def get_log_file_path() -> str:
    """Trả về đường dẫn tuyệt đối đến file log hiện tại."""
    return os.path.abspath(os.path.join(settings.LOG_DIR, settings.LOG_FILE))
