"""
app/main.py
Main entry point of the FastAPI application.

Responsibilities:
  - Initialize the FastAPI app with lifespan (load AI models on startup)
  - Attach middleware (CORS)
  - Mount static files (Frontend HTML)
  - Include API v1 router
  - Backward-compat routes for old /recognize, /register, /logs
"""
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
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
# Lifespan: load AI models BEFORE receiving the first request
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / Shutdown lifecycle handler."""
    logger.info("=" * 60)
    logger.info("INSIGHTFACE API — STARTING UP")
    logger.info("=" * 60)

    # 1. Initialize AI Engine (load model into RAM/VRAM)
    engine = FaceEngine.get_instance()
    engine.initialize()

    # 2. Initialize Face Database (load or bootstrap from data/)
    db = FaceDatabase.get_instance()
    db.initialize(face_engine=engine)

    logger.info("=" * 60)
    logger.info("✅ SERVER READY — Port: %d | Host: %s", settings.APP_PORT, settings.APP_HOST)
    logger.info("=" * 60)

    yield  # ← Server is running (receiving requests)

    # Shutdown
    logger.info("Server is shutting down...")


# ============================================================
# Create FastAPI App
# ============================================================

app = FastAPI(
    title="InsightFace Recognition API",
    description=(
        "Face recognition API integrated with InsightFace + Anti-Spoofing (MiniFASNet). "
        "Supports real-time registration and recognition."
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
# Global Exception Handlers — return consistent JSON
# ============================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Normalize all HTTPErrors into a consistent JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": exc.status_code,
            "detail": exc.detail,
        },
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return 422 validation errors as standardized JSON."""
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "code": 422,
            "detail": "Invalid input data.",
            "errors": exc.errors(),
        },
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
# Backward-Compatible Routes (keep compatibility with old clients)
# ============================================================

@app.get("/", tags=["Health"])
def health_check():
    """Check if the server is running."""
    return {
        "message": "InsightFace API is running.",
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
# Dev runner (run directly: python -m app.main)
# ============================================================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower(),
    )
