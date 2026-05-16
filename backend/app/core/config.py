from pathlib import Path


SECRET_KEY = "test_123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SENTIMENT_MODEL_PATH = BASE_DIR / "train" / "models" / "sentiment_model.joblib"
