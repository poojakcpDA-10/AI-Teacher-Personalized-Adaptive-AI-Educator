import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.config import settings
from app.services import rag_service

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_EXT = {"pdf", "docx", "pptx", "txt"}


def _process_document(document_id: str, student_id: str, path: str, filename: str, filetype: str):
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        doc = db.query(models.Document).get(document_id)
        try:
            num_chunks = rag_service.ingest_document(student_id, document_id, filename, path, filetype)
            doc.num_chunks = num_chunks
            doc.status = "ready" if num_chunks > 0 else "failed"
        except Exception:
            doc.status = "failed"
        db.commit()
    finally:
        db.close()


@router.post("/upload", response_model=schemas.DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    student_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    student = db.query(models.Student).get(student_id)
    if not student:
        raise HTTPException(404, "Student not found")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Unsupported file type '.{ext}'. Allowed: {sorted(ALLOWED_EXT)}")

    doc = models.Document(student_id=student_id, filename=file.filename, filetype=ext, status="processing")
    db.add(doc)
    db.commit()
    db.refresh(doc)

    dest_path = os.path.join(settings.UPLOAD_DIR, f"{doc.id}.{ext}")
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    background_tasks.add_task(_process_document, doc.id, student_id, dest_path, file.filename, ext)
    return doc


@router.get("/{document_id}", response_model=schemas.DocumentOut)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(models.Document).get(document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc
