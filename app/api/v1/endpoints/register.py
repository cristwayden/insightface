"""
app/api/v1/endpoints/register.py
POST /api/v1/register — Registers a new face into the system.
"""
import io
import os

import cv2
import numpy as np
import uuid

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
    name: str = Form(..., description="Employee Name"),
    emp_id: str | None = Form(None, description="Employee ID (Auto-generated UUID if empty)"),
    files: list[UploadFile] = File(..., description="Portrait images of the employee from different angles"),
    engine: FaceEngine = Depends(get_face_engine),
    db: FaceDatabase = Depends(get_face_db),
) -> JSONResponse:
    if not emp_id or not emp_id.strip():
        emp_id = str(uuid.uuid4())
    else:
        emp_id = emp_id.strip()

    client_ip = request.client.host
    logger.info(
        "[REGISTER] Registration request from IP: %s | ID: '%s' | Name: '%s'", client_ip, emp_id, name
    )

    try:
        # --- Read & decode images ---
        embeddings = []
        best_img_bgr = None
        
        for file in files:
            contents = await file.read()
            image = Image.open(io.BytesIO(contents)).convert("RGB")
            img_np = np.array(image)
            img_bgr = img_np[:, :, ::-1].copy()

            faces = engine.get_faces(img_bgr)
            if faces:
                embeddings.append(faces[0].embedding)
                if best_img_bgr is None:
                    best_img_bgr = img_bgr

        if not embeddings:
            logger.warning(
                "[REGISTER] IP: %s | ID: '%s' | Name: '%s' | FAILED: No face detected in any image.",
                client_ip, emp_id, name,
            )
            return JSONResponse(
                content=RegisterResponse(
                    status="error",
                    message="No face detected in the images. Please retake the photos.",
                ).model_dump()
            )

        # Average embeddings
        avg_embedding = np.mean(embeddings, axis=0)
        avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)
        
        # --- Check if face already exists ---
        embedding = avg_embedding
        matched_emp_id, matched_name, score = db.match_face(embedding)
        
        if matched_emp_id is not None and matched_emp_id != emp_id:
            logger.warning(
                "[REGISTER] IP: %s | ID: '%s' | Name: '%s' | FAILED: Face matches ID '%s' (Score: %.4f).",
                client_ip, emp_id, name, matched_emp_id, score
            )
            return JSONResponse(
                content=RegisterResponse(
                    status="error",
                    message=f"This face is already registered under the ID '{matched_emp_id}' ({matched_name}). You cannot register it under a different ID.",
                ).model_dump(),
                status_code=400,
            )

        # --- Save embedding to DB ---
        total = db.add_face(emp_id, name, embedding)

        # --- Save best original image to data/ for backup ---
        os.makedirs(settings.DATA_DIR, exist_ok=True)
        save_path = os.path.join(settings.DATA_DIR, f"{emp_id}_{name}.jpg")
        cv2.imwrite(save_path, best_img_bgr)

        logger.info(
            "[REGISTER] ✅ Registration successful | ID: '%s' | Name: '%s' | IP: %s | Total DB: %d people.",
            emp_id, name, client_ip, total,
        )
        return JSONResponse(
            content=RegisterResponse(
                status="success",
                message=f"Registration successful: [{emp_id}] {name}",
            ).model_dump()
        )

    except Exception as exc:
        logger.error(
            "[REGISTER] ERROR from IP %s | ID: '%s' | Name: '%s' | %s",
            client_ip, emp_id, name, str(exc), exc_info=True,
        )
        return JSONResponse(
            content={"status": "error", "message": str(exc)},
            status_code=500,
        )


@router.post(
    "/analyze_pose",
    summary="Analyze head pose",
    description="Analyzes a single frame and returns the head pose (pitch, yaw, roll).",
)
async def analyze_pose(
    file: UploadFile = File(...),
    engine: FaceEngine = Depends(get_face_engine),
) -> JSONResponse:
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        img_np = np.array(image)
        img_bgr = img_np[:, :, ::-1].copy()

        faces = engine.get_faces(img_bgr)
        if not faces:
            return JSONResponse(content={"has_face": False})

        pose = faces[0].pose  # [pitch, yaw, roll]
        return JSONResponse(
            content={
                "has_face": True,
                "pose": [float(p) for p in pose]
            }
        )
    except Exception as exc:
        logger.error("[ANALYZE_POSE] ERROR: %s", str(exc))
        return JSONResponse(content={"has_face": False, "error": str(exc)})
