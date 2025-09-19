from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class DocumentRecord:
    text: str
    summary_points: Optional[list] = None


_DOCUMENTS: Dict[str, DocumentRecord] = {}


def save_document(document_id: str, text: str) -> None:
    _DOCUMENTS[document_id] = DocumentRecord(text=text)


def get_document_text(document_id: str) -> Optional[str]:
    rec = _DOCUMENTS.get(document_id)
    return rec.text if rec else None


def save_summary(document_id: str, summary_points: list) -> None:
    rec = _DOCUMENTS.get(document_id)
    if rec:
        rec.summary_points = summary_points
    else:
        _DOCUMENTS[document_id] = DocumentRecord(text="", summary_points=summary_points)


def get_summary(document_id: str) -> Optional[list]:
    rec = _DOCUMENTS.get(document_id)
    return rec.summary_points if rec else None


