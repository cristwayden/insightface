"""
app/api/v1/router.py
Gộp tất cả endpoints của API v1 vào một router chính.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import logs, recognize, register

api_v1_router = APIRouter()

api_v1_router.include_router(recognize.router, tags=["Recognition"])
api_v1_router.include_router(register.router, tags=["Registration"])
api_v1_router.include_router(logs.router, tags=["Monitoring"])
