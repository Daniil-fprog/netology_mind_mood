from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORS_ALLOWED_ORIGINS
from app.db.database import Base, engine, SessionLocal
from app.api.routers import analytics, auth, notes, recommendations, users
from app.db.seed import seed_admin_user, seed_test_data
from app import models


# Создаём таблицы, если их ещё нет
Base.metadata.create_all(bind=engine)


# Заполняем БД тестовыми данными
db = SessionLocal()
try:
    seed_admin_user(db)
    seed_test_data(db)
finally:
    db.close()


# === Инициализация FastAPI ===
app = FastAPI(title="MindMOOD App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/home")
def home():
    return {"message": "FastAPI работает"}


# Роуты
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(notes.router)
app.include_router(recommendations.router)
app.include_router(analytics.router)
