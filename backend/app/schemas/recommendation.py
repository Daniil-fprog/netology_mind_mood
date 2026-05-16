from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RecommendationCreate(BaseModel):
    rec_name: str
    rec_text: str
    mood_type: str  # positive / negative


class RecommendationOut(BaseModel):
    id: int
    rec_name: str
    rec_text: str
    mood_type: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)