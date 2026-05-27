from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.note import NoteModel
from app.models.user import UserModel


# Сопоставление sentiment_label с категориями эмоций
def get_emotion_category(sentiment_label: Optional[str]) -> str:
    """Классифицирует sentiment_label в категорию эмоций"""
    if not sentiment_label:
        return "neutral"
    
    sentiment_lower = sentiment_label.lower()
    
    if "posit" in sentiment_lower or "happy" in sentiment_lower:
        return "positive"
    elif "negat" in sentiment_lower or "anxiety" in sentiment_lower or "stress" in sentiment_lower:
        return "negative"
    elif "calm" in sentiment_lower or "neutral" in sentiment_lower:
        return "calm"
    elif "focus" in sentiment_lower or "tired" in sentiment_lower:
        return sentiment_lower
    
    return "neutral"


def calculate_average_mood_index(notes: list[NoteModel]) -> float:
    """Вычисляет средний индекс настроения"""
    if not notes:
        return 0.0
    
    valid_scores = [
        note.sentiment_score 
        for note in notes 
        if note.sentiment_score is not None
    ]
    
    if not valid_scores:
        return 0.0
    
    return round(sum(valid_scores) / len(valid_scores), 1)


def get_mood_chart_data(notes: list[NoteModel], days: int = 7) -> list[dict]:
    """Получает данные для графика настроения за указанный период"""
    if not notes:
        return []
    
    # Фильтруем и сортируем заметки
    filtered_notes = [
        note for note in notes 
        if note.sentiment_score is not None and note.created_at is not None
    ]
    
    if not filtered_notes:
        return []
    
    # Группируем по дням
    daily_scores = {}
    daily_labels = {}
    
    for note in filtered_notes:
        day_key = note.created_at.strftime("%Y-%m-%d")
        if day_key not in daily_scores:
            daily_scores[day_key] = []
            daily_labels[day_key] = note.created_at.strftime("%A")
        daily_scores[day_key].append(note.sentiment_score)
    
    # Считаем среднее по каждому дню
    chart_data = []
    for day_key in sorted(daily_scores.keys())[-days:]:
        scores = daily_scores[day_key]
        avg_score = round(sum(scores) / len(scores), 1)
        
        # Определяем текстовую метку на основе среднего балла
        if avg_score >= 7:
            label = "positive"
        elif avg_score >= 4:
            label = "calm"
        else:
            label = "negative"
        
        # День недели на русском
        day_names = {
            "Monday": "ПН", "Tuesday": "ВТ", "Wednesday": "СР",
            "Thursday": "ЧТ", "Friday": "ПТ", "Saturday": "СБ", "Sunday": "ВС"
        }
        day_name = day_names.get(daily_labels[day_key], day_key)
        
        chart_data.append({
            "date": day_key,
            "day_name": day_name,
            "score": avg_score,
            "label": label
        })
    
    return chart_data


def get_emotion_distribution(notes: list[NoteModel]) -> dict:
    """Получает распределение эмоций"""
    if not notes:
        return {"calm": 0, "focus": 0, "tired": 0, "stress": 0, "positive": 0, "negative": 0, "neutral": 0}
    
    categories = {"calm": 0, "focus": 0, "tired": 0, "stress": 0, "positive": 0, "negative": 0, "neutral": 0}
    
    for note in notes:
        category = get_emotion_category(note.sentiment_label)
        categories[category] = categories.get(category, 0) + 1
    
    # Считаем проценты
    total = len(notes)
    return {key: round((count / total) * 100, 1) for key, count in categories.items()}


def get_neural_insights(notes: list[NoteModel]) -> list[str]:
    """Генерирует нейро-инсайты на основе заметок"""
    if not notes:
        return [
            "Недостаточно данных для анализа. Добавьте больше заметок для получения инсайтов.",
            "Рекомендуется записывать мысли ежедневно для более точного анализа."
        ]
    
    insights = []
    
    # Подсчет категорий
    categories = {"calm": 0, "focus": 0, "tired": 0, "stress": 0, "positive": 0, "negative": 0, "neutral": 0}
    for note in notes:
        category = get_emotion_category(note.sentiment_label)
        categories[category] = categories.get(category, 0) + 1
    
    total = len(notes)
    
    # Инсайт о спокойствии
    if categories["calm"] > total * 0.4:
        insights.append(
            "Ваш уровень спокойствия высок. Вы эффективно управляете эмоциями и сохраняете ресурс."
        )
    
    # Инсайт о позитиве
    if categories["positive"] > total * 0.3:
        insights.append(
            "Позитивные записи преобладают. Это указывает на хорошее эмоциональное состояние."
        )
    
    # Инсайт о усталости
    if categories["tired"] > total * 0.25:
        insights.append(
            "Заметно повышение усталости. Рекомендуется планировать больше времени для отдыха."
        )
    
    # Инсайт о тревоге/стрессе
    if categories["stress"] + categories["negative"] > total * 0.3:
        insights.append(
            "Повышенный уровень стресса и тревоги. Рассмотрите возможность добавления практик релаксации."
        )
    
    # Если инсайтов нет, добавляем общий
    if not insights:
        insights.append(
            "Состояние стабильное без ярко выраженных тенденций. Продолжайте вести дневник для отслеживания изменений."
        )
    
    return insights


def get_notes_for_export(
    current_user: UserModel,
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> list[NoteModel]:
    """Получает заметки пользователя с фильтрацией по дате"""
    query = db.query(NoteModel).filter(NoteModel.user_id == current_user.id)
    
    if start_date:
        query = query.filter(NoteModel.created_at >= start_date)
    
    if end_date:
        query = query.filter(NoteModel.created_at <= end_date)
    
    query = query.order_by(NoteModel.created_at.desc())
    
    return query.all()


def get_analytics_data(
    current_user: UserModel,
    db: Session,
    days: int = 7
) -> dict:
    """Получает полную аналитику для пользователя"""
    notes = get_current_user_notes_service(current_user, db)
    
    return {
        "average_mood_index": calculate_average_mood_index(notes),
        "mood_chart_data": get_mood_chart_data(notes, days),
        "emotion_distribution": get_emotion_distribution(notes),
        "neural_insights": get_neural_insights(notes),
        "notes": notes
    }


# Импорт из note_service
def get_current_user_notes_service(
    current_user: UserModel,
    db: Session,
) -> list[NoteModel]:
    return db.query(NoteModel).filter(NoteModel.user_id == current_user.id).all()
