"""
app/services/face_engine.py
FaceEngine — Singleton quản lý toàn bộ AI model:
  - InsightFace (nhận diện & embedding)
  - Anti-Spoofing (MiniFASNet từ src/)

Model được load MỘT LẦN DUY NHẤT khi startup (lifespan event trong main.py),
sau đó được inject vào các route qua FastAPI Depends.
"""
import os
import warnings
import numpy as np

from app.core.config import settings
from app.core.logging import get_logger

warnings.filterwarnings("ignore")

logger = get_logger(__name__)


class FaceEngine:
    """
    Singleton bọc InsightFace + Anti-Spoofing model.
    Khởi tạo qua FaceEngine.initialize() khi server start.
    """

    _instance: "FaceEngine | None" = None

    def __init__(self) -> None:
        self._insight_app = None
        self._anti_spoof = None
        self._image_cropper = None
        self._ready = False

    # ------------------------------------------------------------------
    # Singleton access
    # ------------------------------------------------------------------

    @classmethod
    def get_instance(cls) -> "FaceEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Initialization (gọi một lần khi startup)
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Load InsightFace và Anti-Spoofing model vào bộ nhớ."""
        if self._ready:
            logger.warning("FaceEngine đã được khởi tạo, bỏ qua.")
            return

        self._load_insightface()
        self._load_anti_spoof()
        self._ready = True
        logger.info("✅ FaceEngine khởi tạo hoàn tất.")

    def _load_insightface(self) -> None:
        logger.info("Đang tải InsightFace model '%s'...", settings.INSIGHTFACE_MODEL)
        from insightface.app import FaceAnalysis  # import lazy để tránh chậm startup nếu không dùng

        det_size = (settings.DET_SIZE, settings.DET_SIZE)
        self._insight_app = FaceAnalysis(
            name=settings.INSIGHTFACE_MODEL,
            providers=["CPUExecutionProvider"],
        )
        self._insight_app.prepare(ctx_id=0, det_size=det_size)
        logger.info("✅ InsightFace model tải xong.")

    def _load_anti_spoof(self) -> None:
        logger.info("Đang tải Anti-Spoofing model...")
        from src.anti_spoof_predict import AntiSpoofPredict
        from src.generate_patches import CropImage

        self._anti_spoof = AntiSpoofPredict(device_id=0)
        self._image_cropper = CropImage()
        logger.info("✅ Anti-Spoofing model tải xong.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_faces(self, img_bgr: np.ndarray) -> list:
        """
        Trả về danh sách face objects từ InsightFace.
        Mỗi face có: .bbox, .embedding
        """
        self._assert_ready()
        return self._insight_app.get(img_bgr)

    def check_liveness(self, img_bgr: np.ndarray, bbox: list) -> tuple[bool, float]:
        """
        Kiểm tra Anti-Spoofing cho một khuôn mặt.

        Args:
            img_bgr: Ảnh gốc BGR
            bbox:    [x1, y1, x2, y2] từ InsightFace

        Returns:
            (is_real: bool, liveness_score: float)
        """
        self._assert_ready()
        from src.utility import parse_model_name

        models_dir = settings.ANTI_SPOOF_MODELS_DIR
        if not os.path.isdir(models_dir):
            logger.warning("Thư mục Anti-Spoof models không tồn tại: %s", models_dir)
            return True, 1.0  # fallback: coi là thật

        model_names = os.listdir(models_dir)
        if not model_names:
            logger.warning("Không tìm thấy model Anti-Spoof trong: %s", models_dir)
            return True, 1.0

        # bbox InsightFace: [x1, y1, x2, y2] → Anti-Spoof cần [x, y, w, h]
        image_bbox = [bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]]
        prediction = np.zeros((1, 3))

        for model_name in model_names:
            h_input, w_input, model_type, scale = parse_model_name(model_name)
            param = {
                "org_img": img_bgr,
                "bbox": image_bbox,
                "scale": scale,
                "out_w": w_input,
                "out_h": h_input,
                "crop": True if scale is not None else False,
            }
            img_crop = self._image_cropper.crop(**param)
            prediction += self._anti_spoof.predict(
                img_crop, os.path.join(models_dir, model_name)
            )

        label = int(np.argmax(prediction))
        score = float(prediction[0][label] / len(model_names))
        is_real = label == 1
        return is_real, score

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _assert_ready(self) -> None:
        if not self._ready:
            raise RuntimeError(
                "FaceEngine chưa được khởi tạo. "
                "Gọi FaceEngine.get_instance().initialize() trước."
            )

    @property
    def is_ready(self) -> bool:
        return self._ready
