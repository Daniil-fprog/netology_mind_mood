from pydantic import BaseModel

from typing import Optional

from datetime import datetime


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

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
