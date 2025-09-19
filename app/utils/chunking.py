from typing import List


def split_text_by_length(text: str, max_chars: int = 4000, overlap: int = 200) -> List[str]:
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + max_chars, text_length)
        chunks.append(text[start:end])
        if end == text_length:
            break
        start = end - overlap
        if start < 0:
            start = 0
    return chunks


