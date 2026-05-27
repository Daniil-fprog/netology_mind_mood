import io
import csv
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import UserModel
from app.schemas.analytics import (
    AnalyticsOut,
    NoteAnalytics,
    NeuralInsights,
    TrendAnalysis
)
from app.services.analytics_service import (
    get_analytics_data,
    get_notes_for_export,
    get_emotion_category,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def notes_to_analytics_list(notes: list) -> list[NoteAnalytics]:
    """Преобразует заметки в список для экспорта"""
    result = []
    for note in notes:
        result.append(NoteAnalytics(
            id=note.id,
            orig_text=note.orig_text,
            sentiment_label=note.sentiment_label,
            sentiment_score=note.sentiment_score,
            created_at=note.created_at
        ))
    return result


@router.get("/", response_model=AnalyticsOut)
def get_analytics(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Получает аналитику по заметкам пользователя за указанный период.
    
    - **days**: Количество дней для анализа (по умолчанию 7)
    """
    analytics_data = get_analytics_data(current_user, db, days)
    
    # Получаем инсайты и данные трендов
    neural_insights_list = analytics_data["neural_insights"]
    trend_analysis = analytics_data.get("trend_analysis", {})
    
    return AnalyticsOut(
        average_mood_index=analytics_data["average_mood_index"],
        mood_chart_data=analytics_data["mood_chart_data"],
        emotion_distribution=analytics_data["emotion_distribution"],
        neural_insights=NeuralInsights(
            insights=neural_insights_list,
            trend_analysis=trend_analysis if trend_analysis else None
        ),
        notes=notes_to_analytics_list(analytics_data["notes"])
    )


@router.get("/export")
def export_analytics_csv(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Экспортирует данные аналитики в CSV файл.
    
    - **days**: Количество дней для экспорта (по умолчанию 7)
    
    Возвращает CSV файл с колонками:
    - ID, Текст, Настроение, Скор, Дата
    """
    notes = get_notes_for_export(current_user, db)
    
    if not notes:
        raise HTTPException(
            status_code=404,
            detail="Нет данных для экспорта. Добавьте заметки для генерации отчета."
        )
    
    # Создаем CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_NONNUMERIC)
    
    # Заголовки
    writer.writerow(['ID', 'Текст', 'Настроение', 'Скор', 'Дата'])
    
    # Данные
    for note in notes:
        emotion = note.sentiment_label or "Не определено"
        score = note.sentiment_score if note.sentiment_score is not None else "-"
        date_str = note.created_at.strftime("%d.%m.%Y %H:%M") if note.created_at else "-"
        
        # Экранируем текст (для CSV с кавычками это делается автоматически)
        writer.writerow([
            note.id,
            note.orig_text,
            emotion,
            score,
            date_str
        ])
    
    output.seek(0)
    
    # Подготовка заголовков для скачивания
    headers = {
        "Content-Disposition": f"attachment; filename=moodsync_analytics_{datetime.now().strftime('%Y%m%d')}.csv"
    }
    
    return StreamingResponse(
        io.StringIO(output.getvalue()),
        media_type="text/csv",
        headers=headers
    )


@router.get("/chart-data")
def get_chart_data(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Получает данные только для графика настроения.
    
    - **days**: Количество дней для анализа (по умолчанию 7)
    """
    notes = get_current_user_notes_service(current_user, db)
    chart_data = get_mood_chart_data(notes, days)
    
    return {"chart_data": chart_data}


@router.get("/distribution")
def get_emotion_distribution(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Получает распределение эмоций по всем заметкам пользователя.
    """
    notes = get_current_user_notes_service(current_user, db)
    distribution = get_emotion_distribution(notes)
    
    return {"distribution": distribution}


# Импорты для функций
from app.services.analytics_service import (
    get_current_user_notes_service,
    get_mood_chart_data,
    get_emotion_distribution,
)
