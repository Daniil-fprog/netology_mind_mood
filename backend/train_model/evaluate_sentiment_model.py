from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

from app.services.sentiment_service import predict_sentimental
from app.services.translation_service import translate_to_english


# Пути
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "train_model" / "data" / "sentiment_test_records.csv"
REPORT_DIR = ROOT_DIR / "train_model" / "reports"

REPORT_CSV_PATH = REPORT_DIR / "sentiment_quality_report.csv"
METRICS_TXT_PATH = REPORT_DIR / "sentiment_quality_metrics.txt"


# Настройки твоей модели
NEGATIVE_CLASS = 0
POSITIVE_CLASS = 1

# Настройки искусственного neutral-класса
NEUTRAL_MIN = 35
NEUTRAL_MAX = 65
BINARY_THRESHOLD = 50


def quote_path(path: Path) -> str:
    """
    Возвращает путь в кавычках, чтобы его было удобно копировать в терминал,
    даже если в директориях есть пробелы.
    """

    return f'"{path}"'


def get_label_by_score(score: int) -> str:
    """
    Определяет 3-классовую метку приложения по sentiment_score.

    0-34   -> negative
    35-65  -> neutral
    66-100 -> positive
    """

    if NEUTRAL_MIN <= score <= NEUTRAL_MAX:
        return "neutral"

    if score < NEUTRAL_MIN:
        return "negative"

    return "positive"


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Не найден файл с тестовыми записями: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH, sep=";")

    required_columns = {"text", "true_label", "true_score"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"В CSV отсутствуют колонки: {missing_columns}")

    rows = []

    for _, row in df.iterrows():
        text = str(row["text"])
        true_score = int(row["true_score"])
        true_label = row["true_label"]

        # 2. Перевод
        translated_text = translate_to_english(text)
        
        sentiment_label, sentiment_score, model_confidence = predict_sentimental(translated_text)

        rows.append(
            {
                "text": text,
                "true_label": true_label,
                "predicted_label": sentiment_label,
                "is_correct": true_label == sentiment_label,
                "true_score": true_score,
                "predicted_score": sentiment_score,
                "score_difference": abs(true_score - sentiment_score),
                "confidence": model_confidence,
            }
        )

    result_df = pd.DataFrame(rows)

    y_true = result_df["true_label"]
    y_pred = result_df["predicted_label"]

    labels = ["negative", "neutral", "positive"]

    accuracy = accuracy_score(y_true, y_pred)

    precision_macro = precision_score(
        y_true,
        y_pred,
        labels=labels,
        average="macro",
        zero_division=0,
    )

    recall_macro = recall_score(
        y_true,
        y_pred,
        labels=labels,
        average="macro",
        zero_division=0,
    )

    f1_macro = f1_score(
        y_true,
        y_pred,
        labels=labels,
        average="macro",
        zero_division=0,
    )

    precision_weighted = precision_score(
        y_true,
        y_pred,
        labels=labels,
        average="weighted",
        zero_division=0,
    )

    recall_weighted = recall_score(
        y_true,
        y_pred,
        labels=labels,
        average="weighted",
        zero_division=0,
    )

    f1_weighted = f1_score(
        y_true,
        y_pred,
        labels=labels,
        average="weighted",
        zero_division=0,
    )

    average_confidence = result_df["confidence"].mean()
    average_score_difference = result_df["score_difference"].mean()

    correct_count = int(result_df["is_correct"].sum())
    incorrect_count = int(len(result_df) - correct_count)

    label_distribution_true = result_df["true_label"].value_counts().to_dict()
    label_distribution_predicted = result_df["predicted_label"].value_counts().to_dict()

    report = classification_report(
        y_true,
        y_pred,
        labels=labels,
        zero_division=0,
    )

    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    matrix_df = pd.DataFrame(matrix, index=labels, columns=labels)

    result_df.to_csv(REPORT_CSV_PATH, index=False, encoding="utf-8-sig")

    metrics_text = f"""
MoodSync — отчёт качества sentiment-модели
=========================================

1. Общая информация
-------------------
Количество тестовых записей: {len(result_df)}
Правильно классифицировано: {correct_count}
Ошибочно классифицировано: {incorrect_count}

2. Основные метрики качества
----------------------------
Accuracy: {accuracy:.4f}
Precision macro: {precision_macro:.4f}
Recall macro: {recall_macro:.4f}
F1-score macro: {f1_macro:.4f}

Precision weighted: {precision_weighted:.4f}
Recall weighted: {recall_weighted:.4f}
F1-score weighted: {f1_weighted:.4f}

3. Метрики sentiment_score
--------------------------
Средняя уверенность модели: {average_confidence:.2f}%
Средняя разница true_score и predicted_score: {average_score_difference:.2f}

4. Распределение реальных классов
---------------------------------
Negative: {label_distribution_true.get("negative", 0)}
Neutral: {label_distribution_true.get("neutral", 0)}
Positive: {label_distribution_true.get("positive", 0)}

5. Распределение предсказанных классов
--------------------------------------
Negative: {label_distribution_predicted.get("negative", 0)}
Neutral: {label_distribution_predicted.get("neutral", 0)}
Positive: {label_distribution_predicted.get("positive", 0)}

6. Confusion matrix
-------------------
Строки — реальные классы.
Столбцы — предсказанные классы.

{matrix_df.to_string()}

7. Classification report
------------------------
{report}

""".strip()

    METRICS_TXT_PATH.write_text(metrics_text, encoding="utf-8")

    print(metrics_text)
    print()


if __name__ == "__main__":
    main()
