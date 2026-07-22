"""
app/api/v1/endpoints/faces.py
CRUD endpoints for managing registered faces in the database.
  GET    /api/v1/faces            — list all faces
  DELETE /api/v1/faces/{emp_id}  — delete a face by ID
  PUT    /api/v1/faces/{emp_id}  — rename a face by ID
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.deps import get_face_db
from app.core.logging import get_logger
from app.services.db_service import FaceDatabase

logger = get_logger(__name__)
router = APIRouter()


class RenameRequest(BaseModel):
    name: str = Field(..., min_length=1, description="New name for the face record")


# ── GET /faces ────────────────────────────────────────────────
@router.get(
    "/faces",
    summary="List all registered faces",
    description="Returns all registered faces (emp_id + name). Embeddings are NOT included.",
)
def list_faces(db: FaceDatabase = Depends(get_face_db)) -> JSONResponse:
    faces = db.list_faces()
    return JSONResponse(content={"status": "success", "total": len(faces), "faces": faces})


# ── DELETE /faces/{emp_id} ────────────────────────────────────
@router.delete(
    "/faces/{emp_id}",
    summary="Delete a face by ID",
    description="Permanently removes the face embedding from the database.",
)
def delete_face(emp_id: str, db: FaceDatabase = Depends(get_face_db)) -> JSONResponse:
    deleted = db.delete_face(emp_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Face ID '{emp_id}' not found.")
    logger.info("[FACES] Deleted face ID: '%s'", emp_id)
    return JSONResponse(content={"status": "success", "message": f"Deleted face ID '{emp_id}'."})


# ── PUT /faces/{emp_id} ───────────────────────────────────────
@router.put(
    "/faces/{emp_id}",
    summary="Rename a face by ID",
    description="Updates the name associated with the given emp_id.",
)
def rename_face(
    emp_id: str,
    body: RenameRequest,
    db: FaceDatabase = Depends(get_face_db),
) -> JSONResponse:
    updated = db.rename_face(emp_id, body.name.strip())
    if not updated:
        raise HTTPException(status_code=404, detail=f"Face ID '{emp_id}' not found.")
    logger.info("[FACES] Renamed face ID: '%s' → '%s'", emp_id, body.name)
    return JSONResponse(
        content={"status": "success", "message": f"Renamed '{emp_id}' to '{body.name}'."}
    )
