"""
app/core/security.py
Xử lý xác thực API Key qua HTTP Header.
Nếu settings.API_KEY để trống → bỏ qua xác thực (development mode).
"""
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

from app.core.config import settings

# Header name mà client cần gửi
API_KEY_HEADER_NAME = "X-API-Key"

_api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


async def verify_api_key(api_key: str | None = Security(_api_key_header)) -> None:
    """
    FastAPI Dependency — xác thực API Key từ header.

    - Nếu settings.API_KEY = "" → bỏ qua, không bắt xác thực.
    - Nếu settings.API_KEY có giá trị → bắt buộc client gửi đúng key.

    Dùng trong route:
        @router.post("/endpoint", dependencies=[Depends(verify_api_key)])
    """
    if not settings.API_KEY:
        # Development mode: không cần API key
        return

    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key. Provide it via 'X-API-Key' header.",
        )
