"""
app/schemas/recognize.py
Pydantic schemas cho endpoint POST /api/v1/recognize.
"""
from pydantic import BaseModel, Field
from typing import List


class FaceResult(BaseModel):
    """Kết quả nhận diện cho một khuôn mặt."""
    name: str = Field(..., description="Tên người được nhận diện, hoặc 'Stranger'")
    score: float = Field(..., ge=0.0, le=1.0, description="Điểm tương đồng cosine (0–1)")
    bbox: List[int] = Field(..., description="Bounding box [x1, y1, x2, y2]")
    is_real: bool = Field(..., description="True nếu khuôn mặt thật (Anti-Spoofing pass)")
    liveness_score: float = Field(..., ge=0.0, le=1.0, description="Điểm sống động (0–1)")


class RecognizeResponse(BaseModel):
    """Response trả về từ endpoint /recognize."""
    status: str = Field(..., description="'success' hoặc 'error'")
    faces: List[FaceResult] = Field(default_factory=list, description="Danh sách khuôn mặt phát hiện được")


class ErrorResponse(BaseModel):
    """Response khi có lỗi."""
    status: str = "error"
    message: str
