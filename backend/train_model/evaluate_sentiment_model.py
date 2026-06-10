import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)
from app.core.config import SENTIMENT_MODEL_PATH


# Чтобы можно было импортировать app.*
ROOT_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = ROOT_DIR.parent

sys.path.append(str(PROJECT_DIR))



DATA_PATH = ROOT_DIR / "train_model" / "data" / "sentiment_test_records.csv"
REPORT_DIR = ROOT_DIR / "train_model" / "reports"

REPORT_CSV_PATH = REPORT_DIR / "sentiment_quality_report.csv"
METRICS_TXT_PATH = REPORT_DIR / "sentiment_quality_metrics.txt"
CONFUSION_MATRIX_CSV_PATH = REPORT_DIR / "confusion_matrix.csv"


LABEL_SCORE_MAP = {
    "negative": 20,
    "neutral": 50,
    "positive": 85,
}


def normalize_label(label) -> str:
    """
    Нормализует метку модели.

    Если модель возвращает:
    0 -> negative
    1 -> positive

    Если модель уже возвращает строку:
    negative / neutral / positive
    """
    if label == 0 or label == "0":
        return "negative"

    if label == 1 or label == "1":
        return "positive"

    label = str(label).strip().lower()

    if label in {"negative", "neutral", "positive"}:
        return label

    return "unknown"


def predict_with_model(model, text: str) -> dict:
    """
    Возвращает предсказание модели:
    - predicted_label
    - predicted_score
    - confidence
    """

    predicted_raw = model.predict([text])[0]
    predicted_label = normalize_label(predicted_raw)

    confidence = None

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba([text])[0]
        classes = list(model.classes_)

        max_probability = float(max(probabilities))
        confidence = round(max_probability * 100, 2)

    predicted_score = LABEL_SCORE_MAP.get(predicted_label, 0)

    return {
        "predicted_label": predicted_label,
        "predicted_score": predicted_score,
        "confidence": confidence,
    }


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Не найден файл с тестовыми записями: {DATA_PATH}")

    if not Path(SENTIMENT_MODEL_PATH).exists():
        raise FileNotFoundError(f"Не найдена модель: {SENTIMENT_MODEL_PATH}")

    df = pd.read_csv(DATA_PATH)

    required_columns = {"text", "true_label", "true_score"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"В CSV отсутствуют колонки: {missing_columns}")

    model = joblib.load(SENTIMENT_MODEL_PATH)

    rows = []

    for _, row in df.iterrows():
        text = str(row["text"])
        true_label = normalize_label(row["true_label"])
        true_score = int(row["true_score"])

        prediction = predict_with_model(model, text)

        predicted_label = prediction["predicted_label"]
        predicted_score = prediction["predicted_score"]
        confidence = prediction["confidence"]

        rows.append(
            {
                "text": text,
                "true_label": true_label,
                "predicted_label": predicted_label,
                "is_correct": true_label == predicted_label,
                "true_score": true_score,
                "predicted_score": predicted_score,
                "score_difference": abs(true_score - predicted_score),
                "confidence": confidence,
            }
        )

    result_df = pd.DataFrame(rows)

    y_true = result_df["true_label"]
    y_pred = result_df["predicted_label"]

    labels = ["negative", "neutral", "positive"]

    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(
        y_true, y_pred, labels=labels, average="macro", zero_division=0
    )
    recall = recall_score(
        y_true, y_pred, labels=labels, average="macro", zero_division=0
    )
    f1 = f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)

    average_confidence = result_df["confidence"].dropna().mean()
    average_score_difference = result_df["score_difference"].mean()

    report = classification_report(
        y_true,
        y_pred,
        labels=labels,
        zero_division=0,
    )

    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    matrix_df = pd.DataFrame(matrix, index=labels, columns=labels)

    result_df.to_csv(REPORT_CSV_PATH, index=False, encoding="utf-8-sig")
    matrix_df.to_csv(CONFUSION_MATRIX_CSV_PATH, encoding="utf-8-sig")

    metrics_text = f"""
MoodSync — отчёт качества sentiment-модели

Количество тестовых записей: {len(result_df)}

Общие метрики:
Accuracy: {accuracy:.4f}
Precision macro: {precision:.4f}
Recall macro: {recall:.4f}
F1-score macro: {f1:.4f}
Average confidence: {average_confidence:.2f}%
Average score difference: {average_score_difference:.2f}

Classification report:

{report}

Confusion matrix:

{matrix_df.to_string()}
""".strip()

    METRICS_TXT_PATH.write_text(metrics_text, encoding="utf-8")

    print(metrics_text)
    print()
    print(f"CSV-отчёт сохранён: {REPORT_CSV_PATH}")
    print(f"Метрики сохранены: {METRICS_TXT_PATH}")
    print(f"Confusion matrix сохранена: {CONFUSION_MATRIX_CSV_PATH}")


if __name__ == "__main__":
    main()
