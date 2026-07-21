"""
app/api/v1/endpoints/register.py
POST /api/v1/register — Registers a new face into the system.
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
    summary="Register face",
    description="Upload a portrait image along with the employee's name to register them in the recognition system.",
)
async def register_face(
    request: Request,
    name: str = Form(..., description="Employee ID or name to register"),
    file: UploadFile = File(..., description="Portrait image of the employee"),
    engine: FaceEngine = Depends(get_face_engine),
    db: FaceDatabase = Depends(get_face_db),
) -> JSONResponse:
    client_ip = request.client.host
    logger.info(
        "[REGISTER] Registration request from IP: %s | Name: '%s'", client_ip, name
    )

    try:
        # --- Read & decode image ---
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        img_np = np.array(image)
        img_bgr = img_np[:, :, ::-1].copy()

        # --- Detect faces ---
        faces = engine.get_faces(img_bgr)
        if not faces:
            logger.warning(
                "[REGISTER] IP: %s | Name: '%s' | FAILED: No face detected.",
                client_ip, name,
            )
            return JSONResponse(
                content=RegisterResponse(
                    status="error",
                    message="No face detected in the image. Please retake the photo.",
                ).model_dump()
            )

        # --- Check if face already exists ---
        embedding = faces[0].embedding
        matched_name, score = db.match_face(embedding)
        
        if matched_name != "Stranger" and matched_name != name:
            logger.warning(
                "[REGISTER] IP: %s | Name: '%s' | FAILED: Face matches '%s' (Score: %.4f).",
                client_ip, name, matched_name, score
            )
            return JSONResponse(
                content=RegisterResponse(
                    status="error",
                    message=f"This face is already registered under the name '{matched_name}'. You cannot register it under a different name.",
                ).model_dump(),
                status_code=400,
            )

        # --- Save embedding to DB ---
        total = db.add_face(name, embedding)

        # --- Save original image to data/ for backup ---
        os.makedirs(settings.DATA_DIR, exist_ok=True)
        save_path = os.path.join(settings.DATA_DIR, f"{name}.jpg")
        cv2.imwrite(save_path, img_bgr)

        logger.info(
            "[REGISTER] ✅ Registration successful | Name: '%s' | IP: %s | Total DB: %d people.",
            name, client_ip, total,
        )
        return JSONResponse(
            content=RegisterResponse(
                status="success",
                message=f"Registration successful: {name}",
            ).model_dump()
        )

    except Exception as exc:
        logger.error(
            "[REGISTER] ERROR from IP %s | Name: '%s' | %s",
            client_ip, name, str(exc), exc_info=True,
        )
        return JSONResponse(
            content={"status": "error", "message": str(exc)},
            status_code=500,
        )
