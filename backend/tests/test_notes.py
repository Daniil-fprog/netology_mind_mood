"""Тесты для роута notes (create, get, update)."""

from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.database import get_db, Base
from app.main import app
from app.models.user import UserModel
from app.models.note import NoteModel


# === Настройка тестовой БД ===
SQLALCHEMY_DATABASE_URL = "sqlite:///./db/test_notes.db"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="function")
def client():
    """Создает тестовый клиент с новой БД для каждого теста."""
    Base.metadata.create_all(bind=test_engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def auth_headers(client):
    """Создает пользователя и возвращает заголовки авторизации."""
    hashed_password = hash_password("testpass123")
    user = UserModel(
        name="Тестовый Пользователь",
        login="testuser",
        password=hashed_password,
    )
    
    db = TestingSessionLocal()
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    
    login_data = {
        "login": "testuser",
        "password": "testpass123",
    }
    response = client.post("/users/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_note_data():
    """Данные для создания заметки."""
    return {
        "orig_text": "Сегодня прекрасный день, хочу прогуляться в парке.",
    }


class TestCreateNote:
    """Тесты эндпоинта POST /notes/."""

    def test_create_note_success(self, client, auth_headers, sample_note_data):
        """Успешное создание заметки."""
        response = client.post("/notes/", json=sample_note_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["orig_text"] == sample_note_data["orig_text"]
        assert "id" in data
        assert "user_id" in data
        assert data["translate_status"] == "pending"

    def test_create_note_empty_text(self, client, auth_headers):
        """Создание заметки с пустым текстом."""
        response = client.post("/notes/", json={"orig_text": ""}, headers=auth_headers)
        
        assert response.status_code == 200

    def test_create_note_missing_text(self, client, auth_headers):
        """Создание заметки без текста."""
        response = client.post("/notes/", json={}, headers=auth_headers)
        
        assert response.status_code == 200

    def test_create_note_unauthorized(self, client, sample_note_data):
        """Создание заметки без авторизации."""
        response = client.post("/notes/", json=sample_note_data)
        
        assert response.status_code == 401


class TestGetNotes:
    """Тесты эндпоинта GET /notes/."""

    def test_get_notes_success(self, client, auth_headers):
        """Успешное получение списка заметок."""
        response = client.get("/notes/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_notes_with_filters(self, client, auth_headers):
        """Получение заметок с фильтрами."""
        query_params = {
            "search": "прогулка",
            "date_from": "2024-01-01",
            "date_to": "2024-12-31",
            "sentiment_label": "positive",
        }
        response = client.get("/notes/", params=query_params, headers=auth_headers)
        
        assert response.status_code == 200

    def test_get_notes_empty_filters(self, client, auth_headers):
        """Получение заметок без фильтров."""
        response = client.get("/notes/", headers=auth_headers)
        
        assert response.status_code == 200

    def test_get_notes_unauthorized(self, client):
        """Получение заметок без авторизации."""
        response = client.get("/notes/")
        
        assert response.status_code == 401


class TestGetNoteById:
    """Тесты эндпоинта GET /notes/{note_id}."""

    def test_get_note_by_id_success(self, client, auth_headers):
        """Успешное получение заметки по ID."""
        note = NoteModel(
            user_id=1,
            orig_text="Текст заметки для теста",
            translate_text="Translation text",
            translate_status="done",
            sentiment_label="positive",
            sentiment_score=75,
        )
        db = TestingSessionLocal()
        db.add(note)
        db.commit()
        db.refresh(note)
        db.close()

        response = client.get(f"/notes/{note.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["orig_text"] == "Текст заметки для теста"
        assert data["id"] == note.id

    def test_get_note_by_id_not_found(self, client, auth_headers):
        """Получение несуществующей заметки по ID."""
        response = client.get("/notes/999999", headers=auth_headers)
        
        assert response.status_code == 404

    def test_get_note_by_id_unauthorized(self, client):
        """Получение заметки без авторизации."""
        response = client.get("/notes/1")
        
        assert response.status_code == 401


class TestUpdateNote:
    """Тесты эндпоинта PATCH /notes/{note_id}."""

    def test_update_note_success(self, client, auth_headers):
        """Успешное обновление заметки."""
        note = NoteModel(
            user_id=1,
            orig_text="Старый текст заметки",
            translate_text="Old translation",
            translate_status="done",
            sentiment_label="neutral",
            sentiment_score=50,
        )
        db = TestingSessionLocal()
        db.add(note)
        db.commit()
        db.refresh(note)
        db.close()

        update_data = {
            "orig_text": "Новый текст заметки обновлен",
        }
        response = client.patch(f"/notes/{note.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["orig_text"] == "Новый текст заметки обновлен"

    def test_update_note_partial(self, client, auth_headers):
        """Частичное обновление заметки (только текст)."""
        note = NoteModel(
            user_id=1,
            orig_text="Оригинальный текст",
            translate_text="Перевод",
            translate_status="done",
        )
        db = TestingSessionLocal()
        db.add(note)
        db.commit()
        db.refresh(note)
        db.close()

        update_data = {
            "orig_text": "Обновленный текст",
        }
        response = client.patch(f"/notes/{note.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["orig_text"] == "Обновленный текст"

    def test_update_note_not_found(self, client, auth_headers):
        """Обновление несуществующей заметки."""
        update_data = {
            "orig_text": "Новый текст",
        }
        response = client.patch("/notes/999999", json=update_data, headers=auth_headers)
        
        assert response.status_code == 404

    def test_update_note_unauthorized(self, client):
        """Обновление заметки без авторизации."""
        update_data = {
            "orig_text": "Новый текст",
        }
        response = client.patch("/notes/1", json=update_data)
        
        assert response.status_code == 401


class TestFilterNotes:
    """Тесты фильтрации заметок."""

    def test_filter_by_sentiment_positive(self, client, auth_headers):
        """Фильтрация по положительным настроениям."""
        note = NoteModel(
            user_id=1,
            orig_text="Отличный день!",
            translate_status="done",
            sentiment_label="positive",
            sentiment_score=85,
        )
        db = TestingSessionLocal()
        db.add(note)
        db.commit()
        db.close()

        response = client.get("/notes/", params={"sentiment_label": "positive"}, headers=auth_headers)
        
        assert response.status_code == 200

    def test_filter_by_sentiment_negative(self, client, auth_headers):
        """Фильтрация по отрицательным настроениям."""
        note = NoteModel(
            user_id=1,
            orig_text="Плохой день",
            translate_status="done",
            sentiment_label="negative",
            sentiment_score=20,
        )
        db = TestingSessionLocal()
        db.add(note)
        db.commit()
        db.close()

        response = client.get("/notes/", params={"sentiment_label": "negative"}, headers=auth_headers)
        
        assert response.status_code == 200

    def test_filter_by_date_range(self, client, auth_headers):
        """Фильтрация по диапазону дат."""
        today = datetime.utcnow()
        yesterday = today - timedelta(days=1)
        
        note1 = NoteModel(
            user_id=1,
            orig_text="Заметка сегодня",
            created_at=today,
            translate_status="done",
        )
        note2 = NoteModel(
            user_id=1,
            orig_text="Заметка вчера",
            created_at=yesterday,
            translate_status="done",
        )
        db = TestingSessionLocal()
        db.add(note1)
        db.add(note2)
        db.commit()
        db.close()

        date_from = yesterday.strftime("%Y-%m-%d")
        date_to = today.strftime("%Y-%m-%d")
        
        response = client.get(
            f"/notes/?date_from={date_from}&date_to={date_to}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
