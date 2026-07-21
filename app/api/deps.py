"""
app/api/deps.py
Dependency Injection providers for FastAPI routes.
Injects FaceEngine and FaceDatabase singletons into each handler.
"""
from app.services.face_engine import FaceEngine
from app.services.db_service import FaceDatabase


def get_face_engine() -> FaceEngine:
    """Returns the pre-initialized FaceEngine singleton."""
    return FaceEngine.get_instance()


def get_face_db() -> FaceDatabase:
    """Returns the pre-loaded FaceDatabase singleton."""
    return FaceDatabase.get_instance()
