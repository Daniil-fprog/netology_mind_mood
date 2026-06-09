import joblib

from app.core.config import SENTIMENT_MODEL_PATH


sentiment_model = joblib.load(SENTIMENT_MODEL_PATH)

# Метки класса
# neutral
# negative
# positive

def calculate_confidence(score: int) -> int:
    neutral_min = 35
    neutral_max = 65

    if neutral_min <= score <= neutral_max:
        center = 50
        distance = abs(score - center)

        return round(distance / 15 * 50)

    if score < neutral_min:
        return round((neutral_min - score) / neutral_min * 50 + 50)

    return round((score - neutral_max) / (100 - neutral_max) * 50 + 50)


def predict_sentimental(text: str) -> tuple[str, int]:
    if not text or not text.strip():
        return "unknown", 0

    probabilities = sentiment_model.predict_proba([text])[0]
    classes = list(sentiment_model.classes_)

    # Твоя модель бинарная:
    # 0 = negative
    # 1 = positive
    negative_class = 0
    positive_class = 1

    if positive_class not in classes:
        print(f"Класс positive={positive_class} отсутствует в sentiment_model.classes_: {classes}")
        return "unknown", 0

    positive_index = classes.index(positive_class)

    # Берем вероятность именно positiv`e-класса
    positive_probability = float(probabilities[positive_index])

    # score теперь означает настроение от 0 до 100:
    # 0 — максимально negative
    # 50 — neutral
    # 100 — максимально positive
    sentiment_score = round(positive_probability * 100)
    # model_confidence = calculate_confidence(sentiment_score)

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

    return sentiment_label, sentiment_score