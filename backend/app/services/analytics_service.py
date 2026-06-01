from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

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


def get_mood_chart_data(notes: list[NoteModel]) -> list[dict]:
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
    for day_key in sorted(daily_scores.keys()):
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


def get_neural_insights(notes: list[NoteModel]) -> dict:
    """
    Генерирует нейро-инсайты на основе заметок с выявлением трендов.
    
    Возвращает словарь с:
    - insights: list[str] - текстовые инсайты
    - trend_analysis: dict - численные данные о трендах
    """
    if not notes:
        return {
            "insights": [
                "Недостаточно данных для анализа. Добавьте больше заметок для получения инсайтов.",
                "Рекомендуется записывать мысли ежедневно для более точного анализа."
            ],
            "trend_analysis": {}
        }

    insights = []
    trend_analysis = {}

    # Получаем все заметки с оценкой настроения
    scored_notes = [n for n in notes if n.sentiment_score is not None and n.created_at is not None]
    
    if len(scored_notes) < 2:
        return {
            "insights": [
                "Недостаточно данных для анализа тенденций. Добавьте больше заметок.",
                "Рекомендуется записывать мысли ежедневно для более точного анализа."
            ],
            "trend_analysis": {}
        }

    # Сортируем по дате
    scored_notes.sort(key=lambda x: x.created_at)

    # Группируем по дням
    daily_scores = {}
    for note in scored_notes:
        day_key = note.created_at.strftime("%Y-%m-%d")
        if day_key not in daily_scores:
            daily_scores[day_key] = []
        daily_scores[day_key].append(note.sentiment_score)

    # Считаем среднее по дням
    daily_averages = []
    for day_key in sorted(daily_scores.keys()):
        scores = daily_scores[day_key]
        avg = round(sum(scores) / len(scores), 1)
        daily_averages.append({"date": day_key, "score": avg})

    if len(daily_averages) < 2:
        insights.append(
            "Недостаточно данных для анализа тенденций. Добавьте больше заметок."
        )
        return {"insights": insights, "trend_analysis": {}}

    # === АНАЛИЗ ТРЕНДОВ ===

    # 1. Сравнение двух последних недель
    current_week = daily_averages[-7:] if len(daily_averages) >= 7 else daily_averages
    previous_week_start = max(0, len(daily_averages) - 14)
    previous_week = daily_averages[previous_week_start:previous_week_start + 7] if len(daily_averages) > 7 else daily_averages[:7]

    current_avg = round(sum(d["score"] for d in current_week) / len(current_week), 1)
    previous_avg = round(sum(d["score"] for d in previous_week) / len(previous_week), 1)

    if previous_avg > 0:
        change_percent = round(((current_avg - previous_avg) / previous_avg) * 100, 1)
    else:
        change_percent = 0

    trend_analysis["current_avg"] = current_avg
    trend_analysis["previous_avg"] = previous_avg
    trend_analysis["change_percent"] = change_percent

    # Инсайт об изменении уровня настроения
    if abs(change_percent) >= 10:
        sign = "вырос" if change_percent > 0 else "снизился"
        insights.append(
            f"Ваш уровень настроения {sign} на {abs(change_percent)}% по сравнению с прошлой неделей."
        )
    elif abs(change_percent) >= 5:
        sign = "вырос" if change_percent > 0 else "снизился"
        insights.append(
            f"Ваш уровень настроения немного {sign} на {abs(change_percent)}% по сравнению с прошлой неделей."
        )

    # 2. Выявление стабильных провалов (дни с низким настроением)
    low_days = [d for d in current_week if d["score"] <= 4]
    if len(low_days) >= 2:
        day_names_rus = {
            "Monday": "Понедельник", "Tuesday": "Вторник", "Wednesday": "Среда",
            "Thursday": "Четверг", "Friday": "Пятница", "Saturday": "Суббота", "Sunday": "Воскресенье"
        }
        low_day_names = []
        for day in low_days:
            # Ищем день недели
            date_obj = datetime.strptime(day["date"], "%Y-%m-%d")
            day_name = day_names_rus.get(date_obj.strftime("%A"), day["date"])
            low_day_names.append(day_name)
        
        if len(low_day_names) >= 3:
            days_str = ", ".join(low_day_names[:2]) + " и другие"
        else:
            days_str = " и ".join(low_day_names)
        insights.append(
            f"В середине недели (в {days_str}) заметны провалы настроения. "
            f"Рекомендуется планировать короткие перерывы или расслабляющие занятия."
        )

    # 3. Выявление подъемов
    high_days = [d for d in current_week if d["score"] >= 8]
    if len(high_days) >= 2:
        insights.append(
            "Отмечены периоды высокого настроения. Это может быть связано с успешными задачами или позитивными событиями."
        )

    # 4. Анализ стабильности (вариабельность)
    scores_list = [d["score"] for d in current_week]
    if len(scores_list) >= 3:
        max_score = max(scores_list)
        min_score = min(scores_list)
        variance = max_score - min_score
        
        if variance <= 2:
            insights.append(
                "Уровень настроения стабильный с небольшой вариабельностью. Вы эффективно управляете эмоциями."
            )
        elif variance <= 4:
            insights.append(
                "Уровень настроения варьируется в умеренных пределах. Это нормальная реакция на разные события."
            )
        else:
            insights.append(
                "Уровень настроения сильно колеблется. Рассмотрите практики для стабилизации эмоционального состояния."
            )

    # 5. Сквозная налаика по изменениям
    if len(daily_averages) >= 3:
        # Считаем направление изменений между днями
        changes = []
        for i in range(1, len(daily_averages)):
            diff = daily_averages[i]["score"] - daily_averages[i-1]["score"]
            changes.append("up" if diff > 0 else ("down" if diff < 0 else "stable"))

        # Ищем устойчивые паттерны
        if all(c == "up" for c in changes[-3:]) and current_avg >= previous_avg:
            insights.append(
                "Отмечается устойчивый рост настроения в последние дни. Продолжайте то, что приносит положительные эмоции."
            )
        elif all(c == "down" for c in changes[-3:]) and current_avg <= previous_avg:
            insights.append(
                "Отмечается устойчивое снижение настроения. Рассмотрите возможность корректировки режима дня или отдыха."
            )

    # 6. Категориальный анализ
    categories = {"calm": 0, "focus": 0, "tired": 0, "stress": 0, "positive": 0, "negative": 0, "neutral": 0}
    for note in notes:
        category = get_emotion_category(note.sentiment_label)
        categories[category] = categories.get(category, 0) + 1

    total = len(notes)

    if categories.get("calm", 0) > total * 0.4:
        insights.append(
            "Ваш уровень спокойствия преобладает. Вы эффективно управляете эмоциями и сохраняете ресурс."
        )

    if categories.get("positive", 0) > total * 0.3:
        insights.append(
            "Позитивные записи преобладают. Это указывает на хорошее эмоциональное состояние."
        )

    if categories.get("tired", 0) > total * 0.25:
        insights.append(
            "Заметно повышение усталости. Рекомендуется планировать больше времени для отдыха и восстановления."
        )

    if categories.get("stress", 0) + categories.get("negative", 0) > total * 0.3:
        insights.append(
            "Повышенный уровень стресса и тревоги. Рассмотрите возможность добавления практик релаксации."
        )

    # Если инсайтов нет, добавляем общий
    if not insights:
        insights.append(
            "Состояние стабильное без ярко выраженных тенденций. Продолжайте вести дневник для отслеживания изменений."
        )

    return {"insights": insights, "trend_analysis": trend_analysis}


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
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> dict:
    """Получает полную аналитику для пользователя"""
    notes = get_current_user_notes_service(current_user, db, start_date, end_date)

    neural_result = get_neural_insights(notes)

    return {
        "average_mood_index": calculate_average_mood_index(notes),
        "mood_chart_data": get_mood_chart_data(notes),
        "emotion_distribution": get_emotion_distribution(notes),
        "neural_insights": neural_result["insights"],
        "trend_analysis": neural_result.get("trend_analysis", {}),
        "notes": notes
    }


# Импорт из note_service
def get_current_user_notes_service(
    current_user: UserModel,
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[NoteModel]:
    query = db.query(NoteModel).filter(NoteModel.user_id == current_user.id)

    if start_date:
        query = query.filter(NoteModel.created_at >= start_date)

    if end_date:
        query = query.filter(NoteModel.created_at <= end_date)

    return query.order_by(NoteModel.created_at.asc()).all()
