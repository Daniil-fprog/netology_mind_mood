from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class NoteAnalytics(BaseModel):
    """Модель заметки с аналитикой для экспорта"""
    id: int
    orig_text: str
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MoodChartPoint(BaseModel):
    """Точка для графика настроения"""
    date: str
    day_name: str
    score: float
    label: Optional[str] = None


class MoodDistribution(BaseModel):
    """Распределение эмоций"""
    calm: float = 0.0
    focus: float = 0.0
    tired: float = 0.0
    stress: float = 0.0
    positive: float = 0.0
    negative: float = 0.0
    neutral: float = 0.0


class AnalyticsOut(BaseModel):
    """Ответ аналитики"""
    average_mood_index: float
    mood_chart_data: list[MoodChartPoint]
    emotion_distribution: MoodDistribution
    neural_insights: list[str]
    notes: list[NoteAnalytics]
