from fastapi import FastAPI
from app.db.database import Base, engine
from app.api.routers import auth, notes, recommendations, users
from app import models


# Создаём таблицы, если их ещё нет
Base.metadata.create_all(bind=engine)

# === Инициализация FastAPI ===
app = FastAPI(title="MindMOOD App")


@app.get("/home")
def home():
    return {"message": "FastAPI работает"}

# Роуты
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(notes.router)
app.include_router(recommendations.router)