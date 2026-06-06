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


class MoodDistribution(BaseModel):
    """Распределение эмоций"""
    calm: float = 0.0
    focus: float = 0.0
    tired: float = 0.0
    stress: float = 0.0
    positive: float = 0.0
    negative: float = 0.0
    neutral: float = 0.0


class TrendAnalysis(BaseModel):
    """Анализ трендов настроения"""
    current_avg: float
    previous_avg: float
    change_percent: float


class NeuralInsights(BaseModel):
    """Нейро-инсайты с анализом трендов"""
    insights: list[str]
    trend_analysis: Optional[Dict[str, Any]] = None


class AnalyticsOut(BaseModel):
    """Ответ аналитики"""
    average_mood_index: float
    mood_chart_data: list[MoodChartPoint]
    emotion_distribution: MoodDistribution
    neural_insights: NeuralInsights
    notes: list[NoteAnalytics]
