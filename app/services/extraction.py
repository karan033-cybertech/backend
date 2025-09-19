from typing import Tuple
import io
import pdfplumber
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import pytesseract


def extract_text_from_pdf(file_bytes: bytes) -> Tuple[str, bool]:
    text_parts: list[str] = []
    ocr_used = False
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text)
            else:
                # Fallback to OCR if page has no extractable text
                ocr_used = True
                image = page.to_image(resolution=300).original
                pil_image = Image.fromarray(image)
                ocr_text = pytesseract.image_to_string(pil_image)
                if ocr_text:
                    text_parts.append(ocr_text)
    # If completely empty, try PyPDF2 as last resort
    if not text_parts:
        reader = PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts), ocr_used


def extract_text_from_docx(file_bytes: bytes) -> str:
    f = io.BytesIO(file_bytes)
    doc = Document(f)
    paragraphs = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(paragraphs)


def extract_text_from_txt(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1", errors="ignore")


