from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models.note import NoteModel
from app.models.user import UserModel


# Функция для выявления повторяющихся паттернов по дням недели
def find_repeated_weekday_patterns(
    daily_averages: list[dict], threshold: int, min_count: int = 2
) -> list[str]:
    """
    Находит дни недели, где значение было зафиксировано минимум min_count раз.

    Args:
        daily_averages: Список средних значений по дням
        threshold: Пороговое значение (например, 40 для провалов, 80 для подъемов)
        min_count: Минимальное количество повторений

    Returns:
        Список названий дней недели (на русском)
    """
    day_names_rus = {
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Saturday": "Суббота",
        "Sunday": "Воскресенье",
    }

    weekday_counts = defaultdict(int)

    for day in daily_averages:
        date_obj = datetime.strptime(day["date"], "%Y-%m-%d")
        weekday_eng = date_obj.strftime("%A")
        weekday_rus = day_names_rus.get(weekday_eng, day["date"])

        if day["score"] <= threshold:
            weekday_counts[weekday_rus] += 1

    # Оставляем только те дни недели, где паттерн был минимум min_count раз
    return [weekday for weekday, count in weekday_counts.items() if count >= min_count]


# Получаем записи для построяние графика
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


# Вычисляет средний индекс настроения и анализ трендов
def calculate_average_mood_index(notes: list[NoteModel]) -> tuple[float, dict]:
    """Вычисляет средний индекс настроения и анализ трендов.

    Возвращает:
        tuple: (средний индекс, данные тренда)
    """
    trend_analysis = {}

    if not notes:
        return (0.0, trend_analysis)

    valid_scores = [
        note.sentiment_score for note in notes if note.sentiment_score is not None
    ]

    if not valid_scores:
        return (0.0, trend_analysis)

    average = round(sum(valid_scores) / len(valid_scores), 1)

    # === АНАЛИЗ ТРЕНДОВ ===
    # Группируем по дням
    daily_scores = {}
    for note in notes:
        if note.sentiment_score is not None and note.created_at is not None:
            day_key = note.created_at.strftime("%Y-%m-%d")
            if day_key not in daily_scores:
                daily_scores[day_key] = []
            daily_scores[day_key].append(note.sentiment_score)

    # Считаем среднее по дням и сортируем
    daily_averages = []
    for day_key in sorted(daily_scores.keys()):
        scores = daily_scores[day_key]
        avg = round(sum(scores) / len(scores), 1)
        daily_averages.append({"date": day_key, "score": avg})

    if len(daily_averages) >= 14:
        # 1. Сравнение двух последних недель
        current_week = daily_averages[-7:]
        previous_week_start = len(daily_averages) - 14
        previous_week = daily_averages[previous_week_start : previous_week_start + 7]

        current_avg = round(
            sum(d["score"] for d in current_week) / len(current_week), 1
        )
        previous_avg = round(
            sum(d["score"] for d in previous_week) / len(previous_week), 1
        )

        if previous_avg > 0:
            change_percent = round(
                ((current_avg - previous_avg) / previous_avg) * 100, 1
            )
        else:
            change_percent = 0

        trend_analysis["current_avg"] = current_avg
        trend_analysis["previous_avg"] = previous_avg
        trend_analysis["change_percent"] = change_percent

    return (average, trend_analysis)


# Функция для получения данных для графика
def get_mood_chart_data(notes: list[NoteModel]) -> list[dict]:
    """Получает данные для графика настроения за указанный период"""
    if not notes:
        return []

    # Фильтруем и сортируем заметки
    filtered_notes = [
        note
        for note in notes
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
            "Monday": "ПН",
            "Tuesday": "ВТ",
            "Wednesday": "СР",
            "Thursday": "ЧТ",
            "Friday": "ПТ",
            "Saturday": "СБ",
            "Sunday": "ВС",
        }
        day_name = day_names.get(daily_labels[day_key], day_key)

        chart_data.append(
            {"date": day_key, "day_name": day_name, "score": avg_score, "label": label}
        )

    return chart_data


# Функция для генерации нейро-инсайтов
def get_neural_insights(notes: list[NoteModel]) -> dict:
    """
    Генерирует нейро-инсайты на основе заметок с выявлением трендов.

    Возвращает словарь с:
    - insights: list[str] - текстовые инсайты
    """
    if not notes:
        return {
            "insights": [
                "Недостаточно данных для анализа. Добавьте больше заметок для получения инсайтов.",
                "Рекомендуется записывать мысли ежедневно для более точного анализа.",
            ],
        }

    insights = []

    # Получаем все заметки с оценкой настроения
    scored_notes = [
        n for n in notes if n.sentiment_score is not None and n.created_at is not None
    ]

    if len(scored_notes) < 2:
        return {
            "insights": [
                "Недостаточно данных для анализа тенденций. Добавьте больше заметок.",
                "Рекомендуется записывать мысли ежедневно для более точного анализа.",
            ],
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
        return {"insights": insights}

    # === АНАЛИЗ ТРЕНДОВ ===

    # 1. Сравнение двух последних недель
    # current_week = daily_averages[-7:] if len(daily_averages) >= 7 else daily_averages
    # previous_week_start = max(0, len(daily_averages) - 14)
    # previous_week = (
    #     daily_averages[previous_week_start : previous_week_start + 7]
    #     if len(daily_averages) > 7
    #     else daily_averages[:7]
    # )

    # current_avg = round(sum(d["score"] for d in current_week) / len(current_week), 1)
    # previous_avg = round(sum(d["score"] for d in previous_week) / len(previous_week), 1)

    # if previous_avg > 0:
    #     change_percent = round(((current_avg - previous_avg) / previous_avg) * 100, 1)
    # else:
    #     change_percent = 0

    # # Инсайт об изменении уровня настроения
    # if abs(change_percent) >= 10:
    #     sign = "вырос" if change_percent > 0 else "снизился"
    #     insights.append(
    #         f"Ваш уровень настроения {sign} на {abs(change_percent)}% по сравнению с прошлой неделей."
    #     )
    # elif abs(change_percent) >= 5:
    #     sign = "вырос" if change_percent > 0 else "снизился"
    #     insights.append(
    #         f"Ваш уровень настроения немного {sign} на {abs(change_percent)}% по сравнению с прошлой неделей."
    #     )

    # 2. Сквозная аналитика по изменениям за последнюю неделю
    # Анализируем только последние 7 дней внутри выбранного периода
    if len(daily_averages) >= 2:
        # Сортируем данные по дате
        sorted_daily_averages = sorted(
            daily_averages, key=lambda d: datetime.strptime(d["date"], "%Y-%m-%d")
        )

        # Берём последнюю дату из доступных данных
        last_date = datetime.strptime(sorted_daily_averages[-1]["date"], "%Y-%m-%d")

        # Начало недельного периода: последние 7 дней включая last_date
        week_start_date = last_date - timedelta(days=6)

        # Оставляем только записи за последние 7 дней
        week_daily_averages = [
            day
            for day in sorted_daily_averages
            if week_start_date
            <= datetime.strptime(day["date"], "%Y-%m-%d")
            <= last_date
        ]

        # Для тренда нужно минимум 2 дня
        if len(week_daily_averages) >= 2:
            total_growth = 0
            total_decline = 0

            for i in range(1, len(week_daily_averages)):
                current_score = week_daily_averages[i]["score"]
                previous_score = week_daily_averages[i - 1]["score"]

                diff = current_score - previous_score

                if diff > 0:
                    total_growth += diff
                elif diff < 0:
                    total_decline += abs(diff)

            trend_score = total_growth - total_decline

            if trend_score > 0:
                insights.append(
                    f"За последнюю неделю наблюдается общий подъём настроения "
                    f"на +{round(trend_score, 1)}%. "
                    f"Это говорит о положительной динамике эмоционального состояния."
                )
            elif trend_score < 0:
                insights.append(
                    f"За последнюю неделю наблюдается общее снижение настроения "
                    f"на {round(trend_score, 1)}%. "
                    f"Стоит обратить внимание на факторы, которые могли повлиять на ухудшение состояния."
                )
            else:
                insights.append(
                    "За последнюю неделю настроение оставалось примерно на одном уровне. "
                    "Резких изменений в эмоциональной динамике не обнаружено."
                )

    # 3. Выявление стабильных провалов (дни с низким настроением)
    # Анализируем по всем данным из выбранного периода
    stable_low_weekdays = find_repeated_weekday_patterns(
        daily_averages, threshold=40, min_count=2
    )

    if stable_low_weekdays:
        if len(stable_low_weekdays) >= 3:
            days_str = ", ".join(stable_low_weekdays[:2]) + " и другие"
        else:
            days_str = " и ".join(stable_low_weekdays)

        insights.append(
            f"В выбранном периоде по дням недели ({days_str}) "
            f"заметны повторяющиеся провалы настроения. "
            f"Рекомендуется заранее планировать короткие перерывы или расслабляющие занятия в эти дни."
        )

    # 4. Выявление подъемов
    # Анализируем по всем данным из выбранного периода
    stable_high_weekdays = find_repeated_weekday_patterns(
        daily_averages, threshold=80, min_count=2
    )

    if stable_high_weekdays:
        if len(stable_high_weekdays) >= 3:
            days_str = ", ".join(stable_high_weekdays[:2]) + " и другие"
        else:
            days_str = " и ".join(stable_high_weekdays)

        insights.append(
            f"В выбранном периоде по дням недели ({days_str}) "
            f"отмечается устойчивое высокое настроение. "
            f"Это может быть связано с успешным выполнением задач или позитивными событиями."
        )

    # 5. Анализ стабильности (вариабельность)
    # Анализируем по всем данным из выбранного периода
    scores_list = [d["score"] for d in daily_averages]
    if len(scores_list) >= 3:
        max_score = max(scores_list)
        min_score = min(scores_list)
        variance = max_score - min_score

        if variance <= 20:
            insights.append(
                "Уровень настроения стабильный с небольшой вариабельностью. Вы эффективно управляете эмоциями."
            )
        elif variance <= 40:
            insights.append(
                "Уровень настроения варьируется в умеренных пределах. Это нормальная реакция на разные события."
            )
        else:
            insights.append(
                "Уровень настроения сильно колеблется. Рассмотрите практики для стабилизации эмоционального состояния."
            )

    # Если инсайтов нет, добавляем общий
    if not insights:
        insights.append(
            "Состояние стабильное без ярко выраженных тенденций. Продолжайте вести дневник для отслеживания изменений."
        )

    return {"insights": insights}


# Для экспорта
def get_notes_for_export(
    current_user: UserModel,
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[NoteModel]:
    """Получает заметки пользователя с фильтрацией по дате"""
    query = db.query(NoteModel).filter(NoteModel.user_id == current_user.id)

    if start_date:
        query = query.filter(NoteModel.created_at >= start_date)

    if end_date:
        query = query.filter(NoteModel.created_at <= end_date)

    query = query.order_by(NoteModel.created_at.desc())

    return query.all()
