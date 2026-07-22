"""
app/schemas/register.py
Pydantic schemas for endpoint POST /api/v1/register.
"""
from pydantic import BaseModel, Field


class RegisterResponse(BaseModel):
    """Response returned from the /register endpoint."""
    status: str = Field(..., description="'success' or 'error'")
    message: str = Field(..., description="Description of the registration result")


class ErrorResponse(BaseModel):
    """Response on error."""
    status: str = "error"
    message: str
