import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Создаём папку db, если её нет
os.makedirs("db", exist_ok=True)

# === Настройка подключения к БД ===
DATABASE_URL = "sqlite:///./db/mood_sync.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для создания таблиц
Base = declarative_base()

# === Получение подключения к БД ===
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()