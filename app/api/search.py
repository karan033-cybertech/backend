from typing import List, Dict
from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import SearchRequest, SearchResponse
from app.storage.memory import get_document_text


router = APIRouter()


def _find_matches(text: str, query: str, window: int = 120) -> List[Dict]:
    lower_text = text.lower()
    lower_q = query.lower()
    results: List[Dict] = []
    start = 0
    while True:
        idx = lower_text.find(lower_q, start)
        if idx == -1:
            break
        a = max(0, idx - window)
        b = min(len(text), idx + len(query) + window)
        snippet = text[a:b]
        results.append({"index": idx, "snippet": snippet})
        start = idx + len(query)
    return results


@router.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    text = get_document_text(req.document_id)
    if text is None:
        raise HTTPException(status_code=404, detail="Document not found")
    matches = _find_matches(text, req.query)
    # Convert matches to the format frontend expects
    results = [match["snippet"] for match in matches]
    return SearchResponse(results=results)


