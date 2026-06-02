"""Тесты для роута analytics (получение данных аналитики)."""

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
SQLALCHEMY_DATABASE_URL = "sqlite:///./db/test_analytics.db"

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
def sample_notes(client):
    """Создает тестовые заметки для аналитики."""
    today = datetime.utcnow()
    notes = []
    
    note_data = [
        {
            "days_ago": 0,
            "text": "Сегодня чувствую себя спокойно.",
            "label": "neutral",
            "score": 62,
        },
        {
            "days_ago": 1,
            "text": "Был продуктивный день!",
            "label": "positive",
            "score": 82,
        },
        {
            "days_ago": 2,
            "text": "Чувствую усталость.",
            "label": "negative",
            "score": 28,
        },
        {
            "days_ago": 3,
            "text": "Настроение нормальное.",
            "label": "neutral",
            "score": 55,
        },
        {
            "days_ago": 4,
            "text": "Тревожно и сложно сосредоточиться.",
            "label": "negative",
            "score": 22,
        },
    ]
    
    for item in note_data:
        created_at = today - timedelta(days=item["days_ago"])
        note = NoteModel(
            user_id=1,
            orig_text=item["text"],
            translate_text="Translation",
            translate_status="done",
            sentiment_label=item["label"],
            sentiment_score=item["score"],
            created_at=created_at,
            updated_at=created_at,
        )
        notes.append(note)
    
    db = TestingSessionLocal()
    for note in notes:
        db.add(note)
    db.commit()
    db.close()
    
    return notes


class TestGetAnalytics:
    """Тесты эндпоинта GET /analytics/."""

    def test_get_analytics_success(self, client, auth_headers, sample_notes):
        """Успешное получение полной аналитики."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        four_days_ago = (datetime.utcnow() - timedelta(days=4)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": four_days_ago,
            "end_date": today,
        }
        response = client.get("/analytics/", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "average_mood_index" in data
        assert "mood_chart_data" in data
        assert "emotion_distribution" in data
        assert "neural_insights" in data
        assert "notes" in data

    def test_get_analytics_empty_period(self, client, auth_headers):
        """Получение аналитики за период без заметок."""
        future_start = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        future_end = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": future_start,
            "end_date": future_end,
        }
        response = client.get("/analytics/", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["average_mood_index"] == 0.0

    def test_get_analytics_invalid_date_range(self, client, auth_headers):
        """Получение аналитики с неверным диапазоном дат."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        past = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": today,
            "end_date": past,
        }
        response = client.get("/analytics/", params=params, headers=auth_headers)
        
        assert response.status_code == 400

    def test_get_analytics_unauthorized(self, client):
        """Получение аналитики без авторизации."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        params = {
            "start_date": today,
            "end_date": today,
        }
        response = client.get("/analytics/", params=params)
        
        assert response.status_code == 401


class TestGetAnalyticsSummary:
    """Тесты эндпоинта GET /analytics/summary."""

    def test_get_summary_success(self, client, auth_headers, sample_notes):
        """Успешное получение краткой сводки."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        four_days_ago = (datetime.utcnow() - timedelta(days=4)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": four_days_ago,
            "end_date": today,
        }
        response = client.get("/analytics/summary", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "average_mood_index" in data
        assert isinstance(data["average_mood_index"], float)

    def test_get_summary_empty_period(self, client, auth_headers):
        """Получение сводки за период без заметок."""
        future_start = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        future_end = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": future_start,
            "end_date": future_end,
        }
        response = client.get("/analytics/summary", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["average_mood_index"] == 0.0

    def test_get_summary_unauthorized(self, client):
        """Получение сводки без авторизации."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        params = {
            "start_date": today,
            "end_date": today,
        }
        response = client.get("/analytics/summary", params=params)
        
        assert response.status_code == 401


class TestExportAnalyticsCSV:
    """Тесты эндпоинта GET /analytics/export."""

    def test_export_csv_success(self, client, auth_headers, sample_notes):
        """Успешный экспорт в CSV."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        four_days_ago = (datetime.utcnow() - timedelta(days=4)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": four_days_ago,
            "end_date": today,
        }
        response = client.get("/analytics/export", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]

    def test_export_csv_empty_data(self, client, auth_headers):
        """Экспорт CSV без данных."""
        future_start = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        future_end = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": future_start,
            "end_date": future_end,
        }
        response = client.get("/analytics/export", params=params, headers=auth_headers)
        
        assert response.status_code == 404

    def test_export_csv_unauthorized(self, client):
        """Экспорт CSV без авторизации."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        params = {
            "start_date": today,
            "end_date": today,
        }
        response = client.get("/analytics/export", params=params)
        
        assert response.status_code == 401


class TestGetChartData:
    """Тесты эндпоинта GET /analytics/chart-data."""

    def test_get_chart_data_success(self, client, auth_headers, sample_notes):
        """Успешное получение данных для графика."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        four_days_ago = (datetime.utcnow() - timedelta(days=4)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": four_days_ago,
            "end_date": today,
        }
        response = client.get("/analytics/chart-data", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "chart_data" in data
        assert isinstance(data["chart_data"], list)

    def test_get_chart_data_empty(self, client, auth_headers):
        """Получение данных для графика без заметок."""
        future_start = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        future_end = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": future_start,
            "end_date": future_end,
        }
        response = client.get("/analytics/chart-data", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["chart_data"] == []

    def test_get_chart_data_unauthorized(self, client):
        """Получение данных графика без авторизации."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        params = {
            "start_date": today,
            "end_date": today,
        }
        response = client.get("/analytics/chart-data", params=params)
        
        assert response.status_code == 401


class TestGetDistribution:
    """Тесты эндпоинта GET /analytics/distribution."""

    def test_get_distribution_success(self, client, auth_headers, sample_notes):
        """Успешное получение распределения эмоций."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        four_days_ago = (datetime.utcnow() - timedelta(days=4)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": four_days_ago,
            "end_date": today,
        }
        response = client.get("/analytics/distribution", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "distribution" in data
        assert isinstance(data["distribution"], dict)

    def test_get_distribution_empty(self, client, auth_headers):
        """Получение распределения без заметок."""
        future_start = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        future_end = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": future_start,
            "end_date": future_end,
        }
        response = client.get("/analytics/distribution", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["distribution"] == {
            "calm": 0.0,
            "focus": 0.0,
            "tired": 0.0,
            "stress": 0.0,
            "positive": 0.0,
            "negative": 0.0,
            "neutral": 0.0,
        }

    def test_get_distribution_unauthorized(self, client):
        """Получение распределения без авторизации."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        params = {
            "start_date": today,
            "end_date": today,
        }
        response = client.get("/analytics/distribution", params=params)
        
        assert response.status_code == 401


class TestGetInsights:
    """Тесты эндпоинта GET /analytics/insights."""

    def test_get_insights_success(self, client, auth_headers, sample_notes):
        """Успешное получение нейро-инсайтов."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        four_days_ago = (datetime.utcnow() - timedelta(days=4)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": four_days_ago,
            "end_date": today,
        }
        response = client.get("/analytics/insights", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data
        assert isinstance(data["insights"], list)

    def test_get_insights_empty(self, client, auth_headers):
        """Получение инсайтов без заметок."""
        future_start = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        future_end = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": future_start,
            "end_date": future_end,
        }
        response = client.get("/analytics/insights", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["insights"] == []

    def test_get_insights_unauthorized(self, client):
        """Получение инсайтов без авторизации."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        params = {
            "start_date": today,
            "end_date": today,
        }
        response = client.get("/analytics/insights", params=params)
        
        assert response.status_code == 401


class TestGetNotesAnalytics:
    """Тесты эндпоинта GET /analytics/notes."""

    def test_get_notes_analytics_success(self, client, auth_headers, sample_notes):
        """Успешное получение списка заметок с аналитикой."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        four_days_ago = (datetime.utcnow() - timedelta(days=4)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": four_days_ago,
            "end_date": today,
        }
        response = client.get("/analytics/notes", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_notes_analytics_empty(self, client, auth_headers):
        """Получение аналитических заметок без данных."""
        future_start = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        future_end = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": future_start,
            "end_date": future_end,
        }
        response = client.get("/analytics/notes", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_notes_analytics_unauthorized(self, client):
        """Получение аналитических заметок без авторизации."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        params = {
            "start_date": today,
            "end_date": today,
        }
        response = client.get("/analytics/notes", params=params)
        
        assert response.status_code == 401
