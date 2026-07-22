"""
app/schemas/recognize.py
Pydantic schemas for endpoint POST /api/v1/recognize.
"""
from pydantic import BaseModel, Field
from typing import List


class FaceResult(BaseModel):
    """Recognition result for a single face."""
    emp_id: str | None = Field(default=None, description="Employee ID")
    name: str = Field(..., description="Name of the recognized person, or 'Stranger'")
    score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score (0-1)")
    bbox: List[int] = Field(..., description="Bounding box [x1, y1, x2, y2]")
    is_real: bool = Field(..., description="True if real face (Anti-Spoofing pass)")
    liveness_score: float = Field(..., ge=0.0, le=1.0, description="Liveness score (0-1)")


class RecognizeResponse(BaseModel):
    """Response returned from the /recognize endpoint."""
    status: str = Field(..., description="'success' or 'error'")
    faces: List[FaceResult] = Field(default_factory=list, description="List of detected faces")


class ErrorResponse(BaseModel):
    """Response on error."""
    status: str = "error"
    message: str
