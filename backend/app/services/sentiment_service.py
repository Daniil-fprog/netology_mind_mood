import joblib

from app.core.config import SENTIMENT_MODEL_PATH


sentiment_model = joblib.load(SENTIMENT_MODEL_PATH)


def predict_sentimental(text: str) -> tuple[str, int]:
    if not text or not text.strip():
        return "unknown", 0

    pred_class = sentiment_model.predict([text])[0]
    probabilities = sentiment_model.predict_proba([text])[0]

    label_map = {
        0: "negative",
        1: "positive",
    }

    if pred_class not in label_map:
        print(f"Неизвестный класс модели: {pred_class}")
        return "unknown", 0

    classes = list(sentiment_model.classes_)

    if pred_class not in classes:
        print(f"Класс {pred_class} отсутствует в sentiment_model.classes_: {classes}")
        return "unknown", 0

    class_index = classes.index(pred_class)
    confidence = probabilities[class_index]

    sentiment_label = label_map[pred_class]
    sentiment_score = round(float(confidence) * 100)

    return sentiment_label, sentiment_score