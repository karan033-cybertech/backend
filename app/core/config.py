import os
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Contract Summariser"
    environment: str = os.getenv("ENV", "development")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    hf_api_key: str | None = os.getenv("HF_API_KEY")
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "20"))
    max_chunk_tokens: int = int(os.getenv("MAX_CHUNK_TOKENS", "1200"))
    model_name: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    enable_ocr: bool = os.getenv("ENABLE_OCR", "true").lower() == "true"


settings = Settings()


