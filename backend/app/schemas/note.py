from pydantic import BaseModel, ConfigDict, field_validator

from typing import Optional, List

from datetime import datetime

from app.schemas.recommendation import RecommendationOutWithNote


class NoteCreate(BaseModel):
    orig_text: str

    @field_validator("orig_text")
    @classmethod
    def validate_orig_text(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Текст записи не может быть пустым")
        if len(v.strip()) < 50:
            raise ValueError(f"Текст записи должен содержать минимум 50 символов. Сейчас: {len(v.strip())} символов")
        return v


class NoteUpdate(BaseModel):
    orig_text: Optional[str] = None


class NoteOut(BaseModel):
    id: int
    user_id: int
    orig_text: str
    translate_text: Optional[str] = None
    translate_status: str

    sentiment_label: Optional[str] = None
    sentiment_score: Optional[int] = None
    model_confidence: Optional[int] = None

    created_at: datetime
    updated_at: datetime

    recommendations: List[RecommendationOutWithNote] = []

    model_config = ConfigDict(from_attributes=True)
