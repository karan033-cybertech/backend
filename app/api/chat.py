from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.storage.memory import get_document_text, get_summary
from app.services.llm import answer_question


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Handle chat questions about contracts"""
    contract_text = get_document_text(req.document_id)
    if contract_text is None:
        raise HTTPException(status_code=404, detail="Document not found")
    
    summary_points = get_summary(req.document_id)
    
    try:
        answer = answer_question(
            contract_text=contract_text,
            question=req.question,
            summary_points=summary_points
        )
        
        return ChatResponse(
            answer=answer,
            citations=None,  # Not implemented yet
            model_name="huggingface"  # Default model name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


