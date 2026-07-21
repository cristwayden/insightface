"""
app/api/v1/endpoints/logs.py
GET /api/v1/logs — Returns the most recent lines from the server log file.
"""
import os

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.core.logging import get_log_file_path, get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/logs",
    summary="View recent logs",
    description="Returns the last N lines from the server log file.",
)
def get_logs(
    lines: int = Query(default=100, ge=1, le=5000, description="Number of log lines to view"),
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
        logger.error("[LOGS] Error reading log file: %s", str(exc))
        return JSONResponse(
            content={"status": "error", "message": str(exc)},
            status_code=500,
        )
