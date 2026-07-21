"""
app/api/v1/router.py
Combines all v1 API endpoints into a main router.

Security:
  - The `verify_api_key` dependency is applied at the ROUTER LEVEL.
  - All endpoints under /api/v1/* require a valid API Key.
  - If API_KEY = "" in .env -> development mode, authentication is skipped.
"""
from fastapi import APIRouter, Depends

from app.api.v1.endpoints import logs, recognize, register
from app.core.security import verify_api_key

# dependencies=[...] here applies to ALL routes included in this router
api_v1_router = APIRouter(
    dependencies=[Depends(verify_api_key)],
)

api_v1_router.include_router(recognize.router, tags=["Recognition"])
api_v1_router.include_router(register.router, tags=["Registration"])
api_v1_router.include_router(logs.router, tags=["Monitoring"])
