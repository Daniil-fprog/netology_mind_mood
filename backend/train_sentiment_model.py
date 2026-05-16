import re
import os
import time
import joblib
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score


def clean_text(text: str) -> str:
    # сюда вставь свою функцию clean_text
    # пример минимальной защиты:
    if not isinstance(text, str):
        return ""

    text = text.lower()  # lowercase
    text = re.sub(r"http\S+", "", text)  # убрать ссылки
    text = re.sub(r"@\w+", "", text)  # убрать @username
    text = re.sub(r"[^a-z\s]", "", text)  # убрать всё кроме букв
    text = re.sub(r"\s+", " ", text).strip()  # лишние пробелы
    return text


start = time.time()
print("Старт обучения модели.\n")

os.makedirs("models", exist_ok=True)

feature_names = ["target", "id", "date", "flag", "user", "text"]

df = pd.read_csv(
    "./data/Sentiment140.csv", sep=",", encoding="latin-1", names=feature_names
)

df["target"] = df["target"].replace({4: 1})
df["text_clean"] = df["text"].apply(clean_text)

X_train, X_test, y_train, y_test = train_test_split(
    df["text_clean"], df["target"], stratify=df["target"], test_size=0.3, random_state=1
)

# Модель
model = Pipeline(
    [
        ("tfidf", TfidfVectorizer(sublinear_tf=True)),
        (
            "logreg",
            LogisticRegression(
                max_iter=1000,
                solver="saga",
                n_jobs=-1,
            ),
        ),
    ]
)

# Лучшие параметры
best_params = {
    "tfidf__ngram_range": (1, 2),
    "tfidf__min_df": 3,
    "tfidf__max_features": 200_000,
    "tfidf__analyzer": "word",
    "logreg__penalty": "l2",
    "logreg__C": 1.0,
}

model.set_params(**best_params)

model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print(classification_report(y_test, y_pred))
print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")

joblib.dump(model, "./models/sentiment_model.joblib")

print("Модель сохранена в ./models/sentiment_model.joblib")
print(f"Время выполнения: {time.time() - start:.2f} сек.")
