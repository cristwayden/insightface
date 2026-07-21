"""
app/api/v1/endpoints/logs.py
GET /api/v1/logs — Trả về các dòng log gần nhất từ file log.
"""
import os

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.core.logging import get_log_file_path, get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/logs",
    summary="Xem log gần đây",
    description="Trả về N dòng log cuối cùng từ file log của server.",
)
def get_logs(
    lines: int = Query(default=100, ge=1, le=5000, description="Số dòng log muốn xem"),
) -> JSONResponse:
    log_file = get_log_file_path()

    if not os.path.exists(log_file):
        return JSONResponse(content={"total_lines": 0, "recent_logs": [], "log_file": log_file})

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()

        recent = all_lines[-lines:]
        return JSONResponse(
            content={
                "total_lines": len(all_lines),
                "returned_lines": len(recent),
                "log_file": log_file,
                "recent_logs": recent,
            }
        )
    except Exception as exc:
        logger.error("[LOGS] Lỗi đọc file log: %s", str(exc))
        return JSONResponse(
            content={"status": "error", "message": str(exc)},
            status_code=500,
        )
