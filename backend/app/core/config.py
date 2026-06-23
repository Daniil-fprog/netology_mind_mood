from pathlib import Path
import os


SECRET_KEY = "test_123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SENTIMENT_MODEL_PATH = BASE_DIR / "train_model" / "models" / "sentiment_model.joblib"

DEFAULT_CORS_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
    "http://139.100.207.142",
    "http://139.100.207.142:8080",
]

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        ",".join(DEFAULT_CORS_ALLOWED_ORIGINS),
    ).split(",")
    if origin.strip()
]
