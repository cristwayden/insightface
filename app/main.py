"""
app/main.py
Entry point chính của ứng dụng FastAPI.

Trách nhiệm:
  - Khởi tạo FastAPI app với lifespan (load AI model khi startup)
  - Gắn middleware (CORS)
  - Mount static files (Frontend HTML)
  - Include API v1 router
  - Backward-compat routes cho /recognize, /register, /logs cũ
"""
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.logging import get_logger
from app.services.db_service import FaceDatabase
from app.services.face_engine import FaceEngine

logger = get_logger(__name__)


# ============================================================
# Lifespan: load AI models TRƯỚC khi nhận request đầu tiên
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / Shutdown lifecycle handler."""
    logger.info("=" * 60)
    logger.info("INSIGHTFACE API — ĐANG KHỞI ĐỘNG")
    logger.info("=" * 60)

    # 1. Khởi tạo AI Engine (load model vào RAM/VRAM)
    engine = FaceEngine.get_instance()
    engine.initialize()

    # 2. Khởi tạo Face Database (load hoặc bootstrap từ data/)
    db = FaceDatabase.get_instance()
    db.initialize(face_engine=engine)

    logger.info("=" * 60)
    logger.info("✅ SERVER SẴN SÀNG — Port: %d | Host: %s", settings.APP_PORT, settings.APP_HOST)
    logger.info("=" * 60)

    yield  # ← Server đang chạy (nhận request)

    # Shutdown
    logger.info("Server đang tắt...")


# ============================================================
# Tạo FastAPI App
# ============================================================

app = FastAPI(
    title="InsightFace Recognition API",
    description=(
        "API nhận diện khuôn mặt tích hợp InsightFace + Anti-Spoofing (MiniFASNet). "
        "Hỗ trợ đăng ký (register) và nhận diện (recognize) theo thời gian thực."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================
# Middleware
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# API Routes v1  →  /api/v1/...
# ============================================================

app.include_router(api_v1_router, prefix="/api/v1")

# ============================================================
# Static Files (Frontend)  →  /static/...
# ============================================================

_static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")


# ============================================================
# Backward-Compatible Routes (giữ tương thích với client cũ)
# ============================================================

@app.get("/", tags=["Health"])
def health_check():
    """Kiểm tra server đang chạy."""
    return {
        "message": "InsightFace API đang hoạt động.",
        "docs": "/docs",
        "version": "2.0.0",
        "endpoints": {
            "recognize": "POST /api/v1/recognize",
            "register":  "POST /api/v1/register",
            "logs":      "GET  /api/v1/logs",
            "frontend":  "GET  /static/index.html",
        },
    }


@app.post("/recognize", include_in_schema=False)
async def compat_recognize():
    """Backward-compat: redirect /recognize → /api/v1/recognize."""
    return RedirectResponse(url="/api/v1/recognize", status_code=307)


@app.post("/register", include_in_schema=False)
async def compat_register():
    """Backward-compat: redirect /register → /api/v1/register."""
    return RedirectResponse(url="/api/v1/register", status_code=307)


@app.get("/logs", include_in_schema=False)
async def compat_logs():
    """Backward-compat: redirect /logs → /api/v1/logs."""
    return RedirectResponse(url="/api/v1/logs", status_code=307)


# ============================================================
# Dev runner (chạy trực tiếp: python -m app.main)
# ============================================================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower(),
    )
