"""
app/core/config.py
Đọc cấu hình từ file .env thông qua pydantic-settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Thư mục gốc của project (thư mục chứa app/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Server ---
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # --- Logging ---
    LOG_LEVEL: str = "DEBUG"
    LOG_DIR: str = "logs"
    LOG_FILE: str = "server.log"
    LOG_MAX_BYTES: int = 5 * 1024 * 1024  # 5 MB
    LOG_BACKUP_COUNT: int = 3

    # --- Paths ---
    DATA_DIR: str = "data"
    RESOURCES_DIR: str = "resources"
    ANTI_SPOOF_MODELS_DIR: str = "resources/anti_spoof_models"
    DB_FILE: str = "data/database.json"

    # --- Face Recognition ---
    SIMILARITY_THRESHOLD: float = 0.45
    INSIGHTFACE_MODEL: str = "buffalo_l"
    DET_SIZE: int = 640  # Detection size (square)

    # --- Security (optional) ---
    API_KEY: str = ""  # Để trống = không bắt xác thực


# Singleton instance — import trực tiếp từ module này
settings = Settings()
