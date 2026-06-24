"""Сервис анализа настроения текста."""

import re
import joblib
from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.core.config import SENTIMENT_MODEL_PATH

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""

    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"[^a-z\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


@lru_cache(maxsize=1)
def get_sentiment_model() -> Optional[object]:
    """Ленивая загрузка модели с кэшированием. Возвращает None если модель не найдена."""
    if not Path(SENTIMENT_MODEL_PATH).exists():
        return None
    return joblib.load(SENTIMENT_MODEL_PATH)


def calculate_confidence(score: int) -> int:
    """Вычисляет уверенность модели на основе sentiment_score (0-100)."""
    neutral_min = 35
    neutral_max = 65

    if neutral_min <= score <= neutral_max:
        center = 50
        distance = abs(score - center)
        return round(distance / 15 * 50)

    if score < neutral_min:
        return round((neutral_min - score) / neutral_min * 50 + 50)

    return round((score - neutral_max) / (100 - neutral_max) * 50 + 50)


def predict_sentimental(text: str) -> tuple[str, int, int]:
    """Предсказывает настроение текста.
    
    Возвращает:
        tuple: (sentiment_label, sentiment_score, model_confidence)
        Если модель не найдена, возвращает заглушку.
    """
    if not text or not text.strip():
        return "unknown", 0, 0

    model = get_sentiment_model()
    
    # Если модель не найдена, возвращаем заглушку
    if model is None:
        return "neutral", 50, 50

    cleaned_text = clean_text(text)
    probabilities = model.predict_proba([cleaned_text])[0]
    classes = list(model.classes_)

    # Твоя модель бинарная:
    # 0 = negative
    # 1 = positive
    negative_class = 0
    positive_class = 1

    if positive_class not in classes:
        print(f"Класс positive={positive_class} отсутствует в sentiment_model.classes_: {classes}")
        return "neutral", 50, 50

    positive_index = classes.index(positive_class)

    # Берем вероятность именно positive-класса
    positive_probability = float(probabilities[positive_index])

    # score теперь означает настроение от 0 до 100:
    # 0 — максимально negative
    # 50 — neutral
    # 100 — максимально positive
    sentiment_score = round(positive_probability * 100)
    model_confidence = calculate_confidence(sentiment_score)

    # neutral — если score около 50
    # Например 50 ± 15 => от 35 до 65
    neutral_margin = 15
    neutral_min = 50 - neutral_margin
    neutral_max = 50 + neutral_margin

    if neutral_min <= sentiment_score <= neutral_max:
        sentiment_label = "neutral"
    elif sentiment_score < neutral_min:
        sentiment_label = "negative"
    else:
        sentiment_label = "positive"

    return sentiment_label, sentiment_score, model_confidence
