import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException
from app.core.config import settings
from app.services.extraction import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
)
from app.storage.memory import save_document
from app.models.schemas import UploadResponse


router = APIRouter()


ALLOWED_EXT = {"pdf", "docx", "txt"}


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)):
    filename = file.filename or "document"
    ext = (filename.split(".")[-1] or "").lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    data = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")

    ocr_used = False
    try:
        if ext == "pdf":
            text, ocr_used = extract_text_from_pdf(data)
        elif ext == "docx":
            text = extract_text_from_docx(data)
        else:
            text = extract_text_from_txt(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction error: {e}")

    if not text or not text.strip():
        raise HTTPException(status_code=422, detail="No text found in document")

    document_id = str(uuid.uuid4())
    save_document(document_id, text)

    return UploadResponse(document_id=document_id, num_characters=len(text), ocr_used=ocr_used)


