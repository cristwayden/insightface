"""
app/schemas/register.py
Pydantic schemas cho endpoint POST /api/v1/register.
"""
from pydantic import BaseModel, Field


class RegisterResponse(BaseModel):
    """Response trả về từ endpoint /register."""
    status: str = Field(..., description="'success' hoặc 'error'")
    message: str = Field(..., description="Mô tả kết quả đăng ký")


class ErrorResponse(BaseModel):
    """Response khi có lỗi."""
    status: str = "error"
    message: str
