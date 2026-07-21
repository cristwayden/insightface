"""
app/api/v1/endpoints/recognize.py
POST /api/v1/recognize — Recognizes faces in an uploaded image.
"""
import io
from datetime import datetime

import numpy as np
from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image

from app.api.deps import get_face_db, get_face_engine
from app.core.logging import get_logger
from app.schemas.recognize import FaceResult, RecognizeResponse
from app.services.db_service import FaceDatabase
from app.services.face_engine import FaceEngine

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/recognize",
    response_model=RecognizeResponse,
    summary="Recognize faces",
    description="Upload an image, returns a list of recognized faces with Anti-Spoofing results.",
)
async def recognize_face(
    request: Request,
    file: UploadFile = File(..., description="Image containing faces to recognize"),
    engine: FaceEngine = Depends(get_face_engine),
    db: FaceDatabase = Depends(get_face_db),
) -> JSONResponse:
    client_ip = request.client.host
    start_time = datetime.now()
    logger.info("[RECOGNIZE] Request from IP: %s | File: %s", client_ip, file.filename)

    try:
        # --- Read & decode image ---
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        img_np = np.array(image)
        img_bgr = img_np[:, :, ::-1].copy()  # RGB -> BGR for OpenCV / InsightFace

        # --- Detection & embedding ---
        faces = engine.get_faces(img_bgr)
        logger.debug("[RECOGNIZE] Detected %d faces.", len(faces))

        results: list[FaceResult] = []
        for face in faces:
            bbox = face.bbox.astype(int).tolist()  # [x1, y1, x2, y2]
            name, score = db.match_face(face.embedding)

            # --- Anti-Spoofing ---
            is_real, liveness_score = engine.check_liveness(img_bgr, bbox)

            liveness_tag = "REAL" if is_real else "⚠ FAKE"
            logger.info(
                "[RECOGNIZE] IP: %s | Name: %s | Match: %.4f | Liveness: %.4f | %s",
                client_ip, name, score, liveness_score, liveness_tag,
            )
            if not is_real:
                logger.warning(
                    "[SECURITY] SPOOFING DETECTED! IP: %s | Name: %s | Liveness: %.4f",
                    client_ip, name, liveness_score,
                )

            results.append(
                FaceResult(
                    name=name,
                    score=round(score, 6),
                    bbox=bbox,
                    is_real=is_real,
                    liveness_score=round(liveness_score, 6),
                )
            )

        if not faces:
            logger.info("[RECOGNIZE] IP: %s | No faces found.", client_ip)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.debug("[RECOGNIZE] Completed in %.3fs", elapsed)

        return JSONResponse(
            content=RecognizeResponse(status="success", faces=results).model_dump()
        )

    except Exception as exc:
        logger.error(
            "[RECOGNIZE] ERROR from IP %s: %s", client_ip, str(exc), exc_info=True
        )
        return JSONResponse(
            content={"status": "error", "message": str(exc)},
            status_code=500,
        )
