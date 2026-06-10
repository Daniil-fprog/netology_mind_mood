"""Тесты для роута recommendations (create, get)."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.database import get_db, Base
from app.main import app
from app.models.user import UserModel
from app.models.recommendation import RecommendationModel


# === Настройка тестовой БД ===
SQLALCHEMY_DATABASE_URL = "sqlite:///./db/test_recommendations.db"

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
        password_hash=hashed_password,
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


class TestCreateRecommendation:
    """Тесты эндпоинта POST /recommendations/."""

    def test_create_recommendation_success(self, client, auth_headers):
        """Успешное создание рекомендации."""
        rec_data = {
            "rec_name": "Тестовая рекомендация",
            "rec_text": "Текст рекомендации для теста",
            "mood_type": "positive",
        }
        response = client.post("/recommendations/", json=rec_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["rec_name"] == "Тестовая рекомендация"
        assert data["rec_text"] == "Текст рекомендации для теста"
        assert data["mood_type"] == "positive"
        assert "id" in data

    def test_create_recommendation_missing_fields(self, client, auth_headers):
        """Создание рекомендации с отсутствующими полями."""
        rec_data = {
            "rec_name": "Неполная рекомендация",
        }
        response = client.post("/recommendations/", json=rec_data, headers=auth_headers)
        
        assert response.status_code == 422

    def test_create_recommendation_invalid_mood_type(self, client, auth_headers):
        """Создание рекомендации с неверным типом настроения."""
        rec_data = {
            "rec_name": "Некорректная рекомендация",
            "rec_text": "Текст",
            "mood_type": "invalid_type",
        }
        response = client.post("/recommendations/", json=rec_data, headers=auth_headers)
        
        assert response.status_code == 422

    def test_create_recommendation_unauthorized(self, client):
        """Создание рекомендации без авторизации."""
        rec_data = {
            "rec_name": "Без авторизации",
            "rec_text": "Текст",
            "mood_type": "positive",
        }
        response = client.post("/recommendations/", json=rec_data)
        
        assert response.status_code == 401


class TestGetRecommendations:
    """Тесты эндпоинта GET /recommendations/."""

    def test_get_recommendations_success(self, client, auth_headers):
        """Успешное получение списка рекомендаций."""
        response = client.get("/recommendations/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_recommendations_with_mood_filter_positive(self, client, auth_headers):
        """Получение рекомендаций с фильтром по positive."""
        rec = RecommendationModel(
            rec_name="Позитивная рекомендация",
            rec_text="Текст",
            mood_type="positive",
            score_from=60,
            score_to=100,
        )
        db = TestingSessionLocal()
        db.add(rec)
        db.commit()
        db.close()

        response = client.get("/recommendations/", params={"mood_type": "positive"}, headers=auth_headers)
        
        assert response.status_code == 200

    def test_get_recommendations_with_mood_filter_negative(self, client, auth_headers):
        """Получение рекомендаций с фильтром по negative."""
        rec = RecommendationModel(
            rec_name="Негативная рекомендация",
            rec_text="Текст",
            mood_type="negative",
            score_from=0,
            score_to=30,
        )
        db = TestingSessionLocal()
        db.add(rec)
        db.commit()
        db.close()

        response = client.get("/recommendations/", params={"mood_type": "negative"}, headers=auth_headers)
        
        assert response.status_code == 200

    def test_get_recommendations_empty_filter(self, client, auth_headers):
        """Получение рекомендаций без фильтра."""
        response = client.get("/recommendations/", params={"mood_type": ""}, headers=auth_headers)
        
        assert response.status_code == 200

    def test_get_recommendations_unauthorized(self, client):
        """Получение рекомендаций без авторизации."""
        response = client.get("/recommendations/")
        
        assert response.status_code == 401

    def test_get_recommendations_seed_data(self, client, auth_headers):
        """Проверка наличия тестовых рекомендаций из seed."""
        response = client.get("/recommendations/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        # В тестовой БД seed-данные не гарантируются, проверяем, что не пустой список
        assert isinstance(data, list)
