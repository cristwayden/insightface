"""
app/services/db_service.py
FaceDatabase — Quản lý toàn bộ vòng đời dữ liệu khuôn mặt:
  - Load/Save từ data/database.json
  - Thêm khuôn mặt mới
  - Tìm kiếm bằng cosine similarity
  - Tự động scan thư mục data/ để bootstrap DB rỗng
"""
import json
import os
import threading

import cv2
import numpy as np

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FaceDatabase:
    """
    Singleton quản lý face embeddings lưu trữ trong database.json.
    Thread-safe qua RLock cho các thao tác read/write.
    """

    _instance: "FaceDatabase | None" = None

    def __init__(self) -> None:
        self._names: list[str] = []
        self._embeddings: list[np.ndarray] = []
        self._lock = threading.RLock()
        self._db_file = settings.DB_FILE
        self._data_dir = settings.DATA_DIR

    # ------------------------------------------------------------------
    # Singleton
    # ------------------------------------------------------------------

    @classmethod
    def get_instance(cls) -> "FaceDatabase":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def initialize(self, face_engine=None) -> None:
        """
        Load DB hoặc bootstrap từ thư mục data/ nếu DB chưa tồn tại.
        face_engine: FaceEngine instance (dùng để bootstrap từ ảnh).
        """
        os.makedirs(self._data_dir, exist_ok=True)

        if self.load():
            return  # DB đã có dữ liệu

        logger.warning(
            "Không tìm thấy database. Đang quét thư mục '%s' để tạo mới...",
            self._data_dir,
        )
        if face_engine is not None:
            self._scan_and_build(face_engine)
        else:
            logger.warning("Không có FaceEngine, bỏ qua bootstrap từ ảnh.")

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------

    def load(self) -> bool:
        """Load database.json. Trả về True nếu tải thành công và có dữ liệu."""
        if not os.path.exists(self._db_file):
            return False

        with self._lock:
            try:
                with open(self._db_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._names = data.get("names", [])
                self._embeddings = [
                    np.array(emb, dtype=np.float32)
                    for emb in data.get("embeddings", [])
                ]
                logger.info(
                    "✅ Đã tải %d khuôn mặt từ database: %s",
                    len(self._names),
                    self._db_file,
                )
                return len(self._names) > 0
            except (json.JSONDecodeError, KeyError) as e:
                logger.error("Lỗi đọc database.json: %s", e)
                return False

    def save(self) -> None:
        """Lưu danh sách hiện tại vào database.json (thread-safe)."""
        with self._lock:
            os.makedirs(self._data_dir, exist_ok=True)
            data = {
                "names": self._names,
                "embeddings": [emb.tolist() for emb in self._embeddings],
            }
            with open(self._db_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.debug("DB đã được lưu: %d record(s).", len(self._names))

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_face(self, name: str, embedding: np.ndarray) -> int:
        """
        Thêm hoặc cập nhật khuôn mặt.
        Nếu tên đã tồn tại → cập nhật embedding.
        Trả về tổng số record sau khi thêm.
        """
        with self._lock:
            if name in self._names:
                idx = self._names.index(name)
                self._embeddings[idx] = embedding
                logger.info("Cập nhật embedding cho: '%s'", name)
            else:
                self._names.append(name)
                self._embeddings.append(embedding)
                logger.info("Đăng ký khuôn mặt mới: '%s'", name)
            self.save()
            return len(self._names)

    def match_face(
        self, target_embedding: np.ndarray, threshold: float | None = None
    ) -> tuple[str, float]:
        """
        Tìm khuôn mặt khớp nhất bằng cosine similarity.

        Returns:
            (name, score) — name = 'Stranger' nếu không khớp.
        """
        th = threshold if threshold is not None else settings.SIMILARITY_THRESHOLD

        with self._lock:
            if not self._embeddings:
                return "Stranger", 0.0

            similarities = [
                self._cosine_similarity(target_embedding, emb)
                for emb in self._embeddings
            ]
            max_idx = int(np.argmax(similarities))
            max_score = float(similarities[max_idx])

            if max_score >= th:
                return self._names[max_idx], max_score
            return "Stranger", max_score

    # ------------------------------------------------------------------
    # Bootstrap
    # ------------------------------------------------------------------

    def _scan_and_build(self, face_engine) -> None:
        """Quét thư mục data/ và đăng ký ảnh có sẵn vào DB mới."""
        registered = 0
        for filename in os.listdir(self._data_dir):
            if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            name = os.path.splitext(filename)[0]
            img_path = os.path.join(self._data_dir, filename)
            img = cv2.imread(img_path)
            if img is None:
                logger.warning("Không đọc được ảnh: %s", img_path)
                continue
            faces = face_engine.get_faces(img)
            if not faces:
                logger.warning("Không phát hiện khuôn mặt trong: %s", img_path)
                continue
            self.add_face(name, faces[0].embedding)
            registered += 1

        if registered > 0:
            logger.info("Bootstrap hoàn tất: đã đăng ký %d khuôn mặt.", registered)
        else:
            logger.info("Không có ảnh hợp lệ trong '%s'. DB trống.", self._data_dir)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._names)
