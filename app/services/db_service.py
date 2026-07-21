"""
app/services/db_service.py
FaceDatabase — Manages the full lifecycle of face data:
  - Load/Save from data/database.json
  - Add new faces
  - Search using cosine similarity
  - Auto-scan the data/ directory to bootstrap an empty DB
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
    Singleton managing face embeddings stored in database.json.
    Thread-safe via RLock for read/write operations.
    """

    _instance: "FaceDatabase | None" = None

    def __init__(self) -> None:
        self._emp_ids: list[str] = []
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
        Load DB or bootstrap from the data/ directory if the DB doesn't exist.
        face_engine: FaceEngine instance (used to bootstrap from images).
        """
        os.makedirs(self._data_dir, exist_ok=True)

        if self.load():
            return  # DB already has data

        logger.warning(
            "Database not found. Scanning directory '%s' to create a new one...",
            self._data_dir,
        )
        if face_engine is not None:
            self._scan_and_build(face_engine)
        else:
            logger.warning("No FaceEngine provided, skipping bootstrap from images.")

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------

    def load(self) -> bool:
        """Load database.json. Returns True if successfully loaded and contains data."""
        if not os.path.exists(self._db_file):
            return False

        with self._lock:
            try:
                with open(self._db_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._names = data.get("names", [])
                self._emp_ids = data.get("emp_ids", self._names.copy())
                self._embeddings = [
                    np.array(emb, dtype=np.float32)
                    for emb in data.get("embeddings", [])
                ]
                logger.info(
                    "✅ Loaded %d faces from database: %s",
                    len(self._names),
                    self._db_file,
                )
                return len(self._names) > 0
            except (json.JSONDecodeError, KeyError) as e:
                logger.error("Error reading database.json: %s", e)
                return False

    def save(self) -> None:
        """Save the current list to database.json (thread-safe)."""
        with self._lock:
            os.makedirs(self._data_dir, exist_ok=True)
            data = {
                "emp_ids": self._emp_ids,
                "names": self._names,
                "embeddings": [emb.tolist() for emb in self._embeddings],
            }
            with open(self._db_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.debug("DB saved: %d record(s).", len(self._names))

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_face(self, emp_id: str, name: str, embedding: np.ndarray) -> int:
        """
        Add or update a face.
        If the emp_id already exists -> updates the embedding.
        Returns the total number of records after adding.
        """
        with self._lock:
            if emp_id in self._emp_ids:
                idx = self._emp_ids.index(emp_id)
                self._names[idx] = name
                self._embeddings[idx] = embedding
                logger.info("Updated embedding for ID: '%s' (Name: '%s')", emp_id, name)
            else:
                self._emp_ids.append(emp_id)
                self._names.append(name)
                self._embeddings.append(embedding)
                logger.info("Registered new face ID: '%s' (Name: '%s')", emp_id, name)
            self.save()
            return len(self._emp_ids)

    def match_face(
        self, target_embedding: np.ndarray, threshold: float | None = None
    ) -> tuple[str | None, str, float]:
        """
        Find the best matching face using cosine similarity.

        Returns:
            (emp_id, name, score) — emp_id = None, name = 'Stranger' if there's no match.
        """
        th = threshold if threshold is not None else settings.SIMILARITY_THRESHOLD

        with self._lock:
            if not self._embeddings:
                return None, "Stranger", 0.0

            similarities = [
                self._cosine_similarity(target_embedding, emb)
                for emb in self._embeddings
            ]
            max_idx = int(np.argmax(similarities))
            max_score = float(similarities[max_idx])

            if max_score >= th:
                return self._emp_ids[max_idx], self._names[max_idx], max_score
            return None, "Stranger", max_score

    # ------------------------------------------------------------------
    # Bootstrap
    # ------------------------------------------------------------------

    def _scan_and_build(self, face_engine) -> None:
        """Scan the data/ directory and register available images into the new DB."""
        registered = 0
        for filename in os.listdir(self._data_dir):
            if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            filename_no_ext = os.path.splitext(filename)[0]
            if "_" in filename_no_ext:
                emp_id, name = filename_no_ext.split("_", 1)
            else:
                emp_id, name = filename_no_ext, filename_no_ext
            
            img_path = os.path.join(self._data_dir, filename)
            img = cv2.imread(img_path)
            if img is None:
                logger.warning("Could not read image: %s", img_path)
                continue
            faces = face_engine.get_faces(img)
            if not faces:
                logger.warning("No face detected in: %s", img_path)
                continue
            self.add_face(emp_id, name, faces[0].embedding)
            registered += 1

        if registered > 0:
            logger.info("Bootstrap complete: registered %d faces.", registered)
        else:
            logger.info("No valid images in '%s'. DB is empty.", self._data_dir)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._emp_ids)
