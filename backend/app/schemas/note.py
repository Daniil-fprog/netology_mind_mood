from pydantic import BaseModel, ConfigDict

from typing import Optional, List

from datetime import datetime

from app.schemas.recommendation import RecommendationOutWithNote


class NoteCreate(BaseModel):
    orig_text: str


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
