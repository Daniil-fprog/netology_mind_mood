import os
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional
from translator import translate_to_english

def translate_note_background(note_id: int):
    """
    Фоновая задача:
    1. Находит заметку по id
    2. Переводит orig_text
    3. Записывает результат в translate_text
    """

    db = SessionLocal()

    try:
        note = db.query(NoteModel).filter(NoteModel.id == note_id).first()

        if note is None:
            print("Заметка не найдена")
            return

        try:
            # print("Начинаю перевод заметки:", note.orig_text)
            translated_text = translate_to_english(note.orig_text)
            # print("Результат перевода:", translated_text)

            note.translate_text = translated_text
            note.translate_status = "done"

        except Exception as e:
            print("Ошибка перевода:", e)
            note.translate_status = "error"

        db.commit()
        db.refresh(note)

    finally:
        db.close()


# Создаём папку db, если её нет
os.makedirs("db", exist_ok=True)


# === Настройка подключения к БД ===
DATABASE_URL = "sqlite:///./db/test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для создания таблиц
Base = declarative_base()


# === Модель sqlalchemy ===
class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    phone = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    notes = relationship("NoteModel", back_populates="user")

# translate_status:
# pending | done | error
# sentiment_label:
# positive / negative / neutral

class NoteModel(Base):
    __tablename__ = "note"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    orig_text = Column(String, nullable=False)
    translate_text = Column(String, nullable=True)
    translate_status = Column(String, default="pending")  # pending | done | error

    sentiment_label = Column(String, nullable=True)
    sentiment_score = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserModel", back_populates="notes")


# Создаём таблицы, если их ещё нет
Base.metadata.create_all(bind=engine)


# === Pydantic схемы ===
class UserCreate(BaseModel):
    phone: str
    name: Optional[str] = None


class UserOut(BaseModel):
    id: int
    phone: str
    name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NoteCreate(BaseModel):
    user_id: int
    orig_text: str


class NoteUpdate(BaseModel):
    orig_text: Optional[str] = None


class NoteOut(BaseModel):
    id: int
    user_id: int
    orig_text: str
    translate_text: Optional[str] = None
    translate_status: str

    sentiment_label: Optional[str] = None
    sentiment_score: Optional[int] = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# === Получение подключения к БД ===
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# === Инициализация FastAPI ===
app = FastAPI(title="MindMOOD App")


@app.get("/home")
def home():
    return {"message": "FastAPI работает"}


# -------------------------
# Пользователи
# -------------------------
@app.post("/users/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация пользователя по номеру телефона
    """

    existing_user = db.query(UserModel).filter(UserModel.phone == user.phone).first()

    if existing_user:
        raise HTTPException(
            status_code=400, detail="Пользователь с таким телефоном уже существует"
        )

    db_user = UserModel(phone=user.phone, name=user.name)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@app.get("/users", response_model=List[UserOut])
def get_users(db: Session = Depends(get_db)):
    """
    Получение всех пользователей
    """

    return db.query(UserModel).all()


@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Получение одного пользователя по id
    """

    user = db.query(UserModel).filter(UserModel.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return user


# -------------------------
# Заметки пользователя
# -------------------------
@app.post("/notes/", response_model=NoteOut)
def create_note(
    note: NoteCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """
    Сохранение новой записи пользователя.
    После сохранения запускается фоновая задача перевода.
    """

    user = db.query(UserModel).filter(UserModel.id == note.user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    db_note = NoteModel(user_id=note.user_id, orig_text=note.orig_text)

    db.add(db_note)
    db.commit()
    db.refresh(db_note)

    # Добавление задачи в фоне
    background_tasks.add_task(translate_note_background, db_note.id)

    return db_note


@app.get("/notes", response_model=List[NoteOut])
def get_notes(db: Session = Depends(get_db)):
    """
    Получение всех записей пользователя
    """

    return db.query(NoteModel).all()


@app.patch("/notes/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    note_data: NoteUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    note = db.query(NoteModel).filter(NoteModel.id == note_id).first()

    if note is None:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    if note_data.orig_text is not None:
        note.orig_text = note_data.orig_text
        note.translate_text = None
        note.translate_status = "pending"

    db.commit()
    db.refresh(note)

    background_tasks.add_task(translate_note_background, note.id)

    return note


@app.get("/users/{user_id}/notes", response_model=List[NoteOut])
def get_user_notes(user_id: int, db: Session = Depends(get_db)):
    """
    Получение всех записей конкретного пользователя
    """

    user = db.query(UserModel).filter(UserModel.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return db.query(NoteModel).filter(NoteModel.user_id == user_id).all()
