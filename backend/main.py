import joblib
import uuid
import os
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from translator import translate_to_english
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext


def predict_sentimental(text: str) -> tuple[str, int]:
    """
    Возвращает:
    - sentiment_label: класс настроения (positive / negative / unknown)
    - sentiment_score: уверенность от 0 до 100
    """

    if not text or not text.strip():
        return "unknown", 0

    pred_class = sentiment_model.predict([text])[0]
    probabilities = sentiment_model.predict_proba([text])[0]

    label_map = {
        0: "negative",
        1: "positive",
    }

    # Проверка, чтобы не записать лишнее в БД
    if pred_class not in label_map:
        print(f"Неизвестный класс модели: {pred_class}")
        return "unknown", 0

    classes = list(sentiment_model.classes_)

    if pred_class not in classes:
        print(f"Класс {pred_class} отсутствует в sentiment_model.classes_: {classes}")
        return "unknown", 0

    class_index = classes.index(pred_class)
    confidence = probabilities[class_index]

    sentiment_label = label_map.get(pred_class)
    sentiment_score = round(float(confidence) * 100)

    return sentiment_label, sentiment_score


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

            sentiment_label, sentiment_score = predict_sentimental(translated_text)

            note.sentiment_label = sentiment_label
            note.sentiment_score = sentiment_score

        except Exception as e:
            print("Ошибка перевода:", e)
            note.translate_status = "error"
            note.sentiment_label = "unknown"
            note.sentiment_score = 0

        db.commit()
        db.refresh(note)

    finally:
        db.close()


# Создаём папку db, если её нет
os.makedirs("db", exist_ok=True)

# Загружаем модель один раз при старте приложения
sentiment_model = joblib.load("./models/sentiment_model.joblib")


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

    name = Column(String, nullable=False)
    login = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    notes = relationship("NoteModel", back_populates="user")


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


class RecommendationModel(Base):
    __tablename__ = "recommendation"

    id = Column(Integer, primary_key=True, index=True)

    rec_name = Column(String, nullable=False)
    rec_class = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Создаём таблицы, если их ещё нет
Base.metadata.create_all(bind=engine)


# === Pydantic схемы ===
class UserCreate(BaseModel):
    name: str
    password: str
    phone: Optional[str] = None


class UserOut(BaseModel):
    id: int
    name: str
    login: str
    phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    login: str
    password: str


# Токен
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Рекомендации
class RecommendationCreate(BaseModel):
    rec_name: str
    mood_type: str  # positive / negative


class RecommendationOut(BaseModel):
    id: int
    rec_name: str
    mood_type: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NoteCreate(BaseModel):
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


SECRET_KEY = "test_123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 дней

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def generate_login(db: Session) -> str:
    """
    Генерирует уникальный логин пользователя.
    Пример: user_a8f31c2d
    """

    while True:
        login = f"user_{uuid.uuid4().hex[:8]}"

        existing_user = db.query(UserModel).filter(UserModel.login == login).first()

        if existing_user is None:
            return login


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Создаёт JWT-токен.
    В data обычно кладём user_id в поле sub.
    """

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Проверяет JWT-токен и возвращает текущего пользователя.
    Если токена нет или он неправильный — отдаёт 401.
    """

    credentials_exception = HTTPException(
        status_code=401,
        detail="Пользователь не авторизован",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (InvalidTokenError, ValueError):
        raise credentials_exception

    user = db.query(UserModel).filter(UserModel.id == user_id).first()

    if user is None:
        raise credentials_exception

    return user


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
    Регистрация пользователя.
    Логин генерируется автоматически.
    Пароль сохраняется в виде хеша.
    """

    if user.phone:
        existing_phone = (
            db.query(UserModel).filter(UserModel.phone == user.phone).first()
        )

        if existing_phone:
            raise HTTPException(
                status_code=400, detail="Пользователь с таким телефоном уже существует"
            )

    generated_login = generate_login(db)

    db_user = UserModel(
        name=user.name,
        login=generated_login,
        password_hash=hash_password(user.password),
        phone=user.phone,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@app.post("/users/login", response_model=TokenOut)
def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Авторизация пользователя по номеру телефона.
    Для MVP: если телефон есть в БД — выдаём токен.
    """

    user = db.query(UserModel).filter(UserModel.login == user_data.login).first()

    if user is None:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    access_token = create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.get("/users", response_model=List[UserOut])
def get_users(
    db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)
):
    """
    Получение всех пользователей
    """

    return db.query(UserModel).all()


@app.get("/users/me", response_model=UserOut)
def get_me(current_user: UserModel = Depends(get_current_user)):
    return current_user


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
    note: NoteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Сохранение новой записи пользователя.
    После сохранения запускается фоновая задача перевода.
    """

    db_note = NoteModel(user_id=current_user.id, orig_text=note.orig_text)

    db.add(db_note)
    db.commit()
    db.refresh(db_note)

    # Добавление задачи в фоне
    background_tasks.add_task(translate_note_background, db_note.id)

    return db_note


@app.get("/notes", response_model=List[NoteOut])
def get_notes(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Получение всех записей пользователя
    """

    return db.query(NoteModel).filter(NoteModel.user_id == current_user.id).all()


@app.patch("/notes/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    note_data: NoteUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    note = (
        db.query(NoteModel)
        .filter(
            NoteModel.id == note_id,
            NoteModel.user_id == current_user.id,
        )
        .first()
    )

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
def get_user_notes(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Получение всех записей конкретного пользователя
    """

    user = db.query(UserModel).filter(UserModel.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return db.query(NoteModel).filter(NoteModel.user_id == user_id).all()
