"""
app/api/v1/endpoints/register.py
POST /api/v1/register — Đăng ký khuôn mặt mới vào hệ thống.
"""
import io
import os

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

from app.api.deps import get_face_db, get_face_engine
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.register import RegisterResponse
from app.services.db_service import FaceDatabase
from app.services.face_engine import FaceEngine

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=RegisterResponse,
    summary="Đăng ký khuôn mặt",
    description="Upload ảnh kèm tên nhân viên để đăng ký vào hệ thống nhận diện.",
)
async def register_face(
    request: Request,
    name: str = Form(..., description="Tên nhân viên cần đăng ký"),
    file: UploadFile = File(..., description="Ảnh chân dung nhân viên"),
    engine: FaceEngine = Depends(get_face_engine),
    db: FaceDatabase = Depends(get_face_db),
) -> JSONResponse:
    client_ip = request.client.host
    logger.info(
        "[REGISTER] Yêu cầu đăng ký từ IP: %s | Tên: '%s'", client_ip, name
    )

    try:
        # --- Đọc & decode ảnh ---
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        img_np = np.array(image)
        img_bgr = img_np[:, :, ::-1].copy()

        # --- Phát hiện khuôn mặt ---
        faces = engine.get_faces(img_bgr)
        if not faces:
            logger.warning(
                "[REGISTER] IP: %s | Tên: '%s' | THẤT BẠI: không phát hiện khuôn mặt.",
                client_ip, name,
            )
            return JSONResponse(
                content=RegisterResponse(
                    status="error",
                    message="Không tìm thấy khuôn mặt trong ảnh. Vui lòng chụp lại.",
                ).model_dump()
            )

        # --- Lưu embedding vào DB ---
        embedding = faces[0].embedding
        total = db.add_face(name, embedding)

        # --- Lưu ảnh gốc vào data/ để backup ---
        os.makedirs(settings.DATA_DIR, exist_ok=True)
        save_path = os.path.join(settings.DATA_DIR, f"{name}.jpg")
        cv2.imwrite(save_path, img_bgr)

        logger.info(
            "[REGISTER] ✅ Đăng ký thành công | Tên: '%s' | IP: %s | Tổng DB: %d người.",
            name, client_ip, total,
        )
        return JSONResponse(
            content=RegisterResponse(
                status="success",
                message=f"Đăng ký thành công: {name}",
            ).model_dump()
        )

    except Exception as exc:
        logger.error(
            "[REGISTER] LỖI từ IP %s | Tên: '%s' | %s",
            client_ip, name, str(exc), exc_info=True,
        )
        return JSONResponse(
            content={"status": "error", "message": str(exc)},
            status_code=500,
        )
