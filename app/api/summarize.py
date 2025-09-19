from fastapi import APIRouter, HTTPException
from app.models.schemas import SummaryRequest, SummaryResponse
from app.storage.memory import get_document_text, save_summary
from app.services.llm import summarize_contract
from app.core.config import settings


router = APIRouter()


@router.post("/summarize", response_model=SummaryResponse)
def summarize(req: SummaryRequest):
    text = get_document_text(req.document_id)
    if text is None:
        raise HTTPException(status_code=404, detail="SummaryRequest")
    points = summarize_contract(text)
    save_summary(req.document_id, points)
    # Return in the format frontend expects
    return SummaryResponse(document_id=req.document_id, summary=points, model_name=settings.model_name)


