from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.schemas.recommendation import RecommendationOutWithNote

class NoteAnalytics(BaseModel):
    """Модель заметки с аналитикой для экспорта"""
    id: int
    orig_text: str
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None
    created_at: datetime

    recommendations: List[RecommendationOutWithNote] = []

    model_config = {"from_attributes": True}


class MoodChartPoint(BaseModel):
    """Точка для графика настроения"""
    date: str
    day_name: str
    score: float
    label: Optional[str] = None


class TrendAnalysis(BaseModel):
    """Анализ трендов настроения"""
    current_avg: float
    previous_avg: float
    change_percent: float


class NeuralInsights(BaseModel):
    """Нейро-инсайты с анализом трендов"""
    insights: list[str]
    trend_analysis: Optional[Dict[str, Any]] = None

ё