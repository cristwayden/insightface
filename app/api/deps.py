"""
app/api/deps.py
Dependency Injection providers cho FastAPI routes.
Inject FaceEngine và FaceDatabase singleton vào từng handler.
"""
from app.services.face_engine import FaceEngine
from app.services.db_service import FaceDatabase


def get_face_engine() -> FaceEngine:
    """Trả về FaceEngine singleton đã được khởi tạo sẵn."""
    return FaceEngine.get_instance()


def get_face_db() -> FaceDatabase:
    """Trả về FaceDatabase singleton đã được load sẵn."""
    return FaceDatabase.get_instance()
