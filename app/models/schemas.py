from typing import List, Optional
from pydantic import BaseModel


class UploadResponse(BaseModel):
    document_id: str
    num_characters: int
    ocr_used: bool


class SummaryRequest(BaseModel):
    document_id: str


class SummaryResponse(BaseModel):
    document_id: str
    summary: List[str]  # Changed from summary_points to match frontend
    model_name: str


class ChatRequest(BaseModel):
    document_id: str
    question: str
    chat_history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    answer: str
    citations: Optional[List[str]] = None
    model_name: str


class SearchRequest(BaseModel):
    document_id: str
    query: str


class SearchResponse(BaseModel):
    results: List[str]  # Changed from matches to results to match frontend


