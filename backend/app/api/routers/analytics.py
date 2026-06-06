import io
import csv
from datetime import date, datetime, time
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
)
from app.services.analytics_service import (
    calculate_average_mood_index,
    get_analytics_data,
    get_notes_for_export,
    get_current_user_notes_service,
    get_mood_chart_data,
    get_neural_insights,
)


router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_date_range(
    start_date: date = Query(
        ..., description="Дата начала периода в формате YYYY-MM-DD"
    ),
    end_date: date = Query(..., description="Дата конца периода в формате YYYY-MM-DD"),
) -> tuple[datetime, datetime]:
    """Возвращает включительный диапазон дат для аналитики."""
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Дата начала периода не может быть позже даты конца периода.",
        )

    return (
        datetime.combine(start_date, time.min),
        datetime.combine(end_date, time.max),
    )


def get_emotion_text(sentiment_label: str | None) -> str:
    mood_map = {
        "negative": "Плохое",
        "positive": "Хорошее",
        "neutral": "Спокойное",
    }

    if not sentiment_label:
        return "Не определено"

    return mood_map.get(sentiment_label.lower(), "Не определено")


def notes_to_analytics_list(notes: list) -> list[NoteAnalytics]:
    result = []

    for note in notes:
        result.append(
            NoteAnalytics(
                id=note.id,
                orig_text=note.orig_text,
                sentiment_label=note.sentiment_label,
                sentiment_score=note.sentiment_score,
                created_at=note.created_at,
                recommendations=note.recommendations,
            )
        )

    return result


@router.get("/export")
def export_analytics_csv(
    date_range: tuple[datetime, datetime] = Depends(get_date_range),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Экспортирует данные аналитики в CSV файл за произвольный период.

    - **start_date**: дата начала периода в формате YYYY-MM-DD
    - **end_date**: дата конца периода в формате YYYY-MM-DD

    Возвращает CSV файл с колонками:
    - ID, Текст, Настроение, Скор, Дата
    """
    start_datetime, end_datetime = date_range
    notes = get_notes_for_export(current_user, db, start_datetime, end_datetime)

    if not notes:
        raise HTTPException(
            status_code=404,
            detail="Нет данных для экспорта. Добавьте заметки для генерации отчета.",
        )

    # Создаем CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_NONNUMERIC)

    max_recommendations = max(len(note.recommendations) for note in notes)

    headers = [
        "ID записи",
        "Дата создания",
        "Текст записи",
        "Эмоциональная окраска",
        "Оценка настроения (0-100)",
    ]

    for i in range(1, max_recommendations + 1):
        headers.extend(
            [
                f"Рекомендация {i}: Название",
                f"Рекомендация {i}: Текст",
            ]
        )

    # Заголовки
    writer.writerow(headers)

    # Данные
    for note in notes:
        row = [
            note.id,
            note.created_at.strftime("%d.%m.%Y %H:%M"),
            note.orig_text,
            get_emotion_text(note.sentiment_label),
            note.sentiment_score if note.sentiment_score is not None else "-",
        ]

        for recommendation in note.recommendations:
            row.extend(
                [
                    recommendation.rec_name,
                    recommendation.rec_text,
                ]
            )

        missing = max_recommendations - len(note.recommendations)

        for _ in range(missing):
            row.extend(["", ""])

        writer.writerow(row)

    output.seek(0)

    # Подготовка заголовков для скачивания
    headers = {
        "Content-Disposition": f"attachment; filename=moodsync_analytics_{datetime.now().strftime('%Y%m%d')}.csv"
    }

    return StreamingResponse(
        io.StringIO(output.getvalue()), media_type="text/csv", headers=headers
    )


@router.get("/", response_model=AnalyticsOut)
def get_analytics(
    date_range: tuple[datetime, datetime] = Depends(get_date_range),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Получает полную аналитику по заметкам пользователя за произвольный период.

    - **start_date**: дата начала периода в формате YYYY-MM-DD
    - **end_date**: дата конца периода в формате YYYY-MM-DD
    """
    start_datetime, end_datetime = date_range
    analytics_data = get_analytics_data(
        current_user,
        db,
        start_datetime,
        end_datetime,
    )

    # Получаем инсайты и данные трендов
    neural_insights_list = analytics_data["neural_insights"]
    trend_analysis = analytics_data.get("trend_analysis", {})

    return AnalyticsOut(
        average_mood_index=analytics_data["average_mood_index"],
        mood_chart_data=analytics_data["mood_chart_data"],
        emotion_distribution=analytics_data["emotion_distribution"],
        neural_insights=NeuralInsights(
            insights=neural_insights_list,
            trend_analysis=trend_analysis if trend_analysis else None,
        ),
        notes=notes_to_analytics_list(analytics_data["notes"]),
    )


@router.get("/summary")
def get_analytics_summary(
    date_range: tuple[datetime, datetime] = Depends(get_date_range),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Получает средний индекс настроения за произвольный период.
    """
    start_datetime, end_datetime = date_range
    notes = get_current_user_notes_service(
        current_user,
        db,
        start_datetime,
        end_datetime,
    )

    return {"average_mood_index": calculate_average_mood_index(notes)}


@router.get("/chart-data")
def get_chart_data(
    date_range: tuple[datetime, datetime] = Depends(get_date_range),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Получает данные только для графика настроения за произвольный период.

    - **start_date**: дата начала периода в формате YYYY-MM-DD
    - **end_date**: дата конца периода в формате YYYY-MM-DD
    """
    start_datetime, end_datetime = date_range
    notes = get_current_user_notes_service(
        current_user,
        db,
        start_datetime,
        end_datetime,
    )
    chart_data = get_mood_chart_data(notes)

    return {"chart_data": chart_data}


@router.get("/distribution")
def get_distribution(
    date_range: tuple[datetime, datetime] = Depends(get_date_range),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Получает распределение эмоций за произвольный период.
    """
    start_datetime, end_datetime = date_range
    notes = get_current_user_notes_service(
        current_user,
        db,
        start_datetime,
        end_datetime,
    )
    distribution = calculate_emotion_distribution(notes)

    return {"distribution": distribution}


@router.get("/insights")
def get_insights(
    date_range: tuple[datetime, datetime] = Depends(get_date_range),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Получает нейро-инсайты и анализ трендов за произвольный период.
    """
    start_datetime, end_datetime = date_range
    notes = get_current_user_notes_service(
        current_user,
        db,
        start_datetime,
        end_datetime,
    )

    return get_neural_insights(notes)


@router.get("/notes", response_model=list[NoteAnalytics])
def get_notes_analytics(
    date_range: tuple[datetime, datetime] = Depends(get_date_range),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Получает список заметок с аналитическими полями за произвольный период.
    """
    start_datetime, end_datetime = date_range
    notes = get_current_user_notes_service(
        current_user,
        db,
        start_datetime,
        end_datetime,
    )

    return notes_to_analytics_list(notes)
