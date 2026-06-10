"""Интеграционные тесты для всего API."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.database import get_db, Base, engine
from app.main import app
from app.models.user import UserModel


# === Настройка тестовой БД ===
SQLALCHEMY_DATABASE_URL = "sqlite:///./db/test_integration.db"

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


class TestFullUserFlow:
    """Полный пользовательский флоу: регистрация -> логин -> работа с заметками."""

    def test_full_user_flow(self, client):
        """Проверяет полный флоу пользователя."""
        # 1. Регистрация
        register_data = {
            "name": "Полный Пользователь",
            "login": "fulluser",
            "password": "password123",
        }
        response = client.post("/users/register", json=register_data)
        
        assert response.status_code == 200
        user_data = response.json()
        user_id = user_data["id"]
        
        # 2. Логин
        login_data = {
            "login": "fulluser",
            "password": "password123",
        }
        response = client.post("/users/login", json=login_data)
        
        assert response.status_code == 200
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Получение профиля
        response = client.get("/users/me", headers=headers)
        assert response.status_code == 200
        
        # 4. Создание заметки
        note_data = {
            "orig_text": "Тестовая заметка через полный флоу. Здесь должно быть не менее пятидесяти символов.",
        }
        response = client.post("/notes/", json=note_data, headers=headers)
        assert response.status_code == 200
        note_id = response.json()["id"]
        
        # 5. Получение заметки
        response = client.get(f"/notes/{note_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["orig_text"] == note_data["orig_text"]
        
        # 6. Обновление заметки
        update_data = {
            "orig_text": "Обновленная заметка",
        }
        response = client.patch(f"/notes/{note_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        assert response.json()["orig_text"] == "Обновленная заметка"
        
        # 7. Получение рекомендаций
        response = client.get("/recommendations/", headers=headers)
        assert response.status_code == 200
        
        # 8. Получение аналитики
        today = "2024-12-31"
        params = {
            "start_date": "2024-01-01",
            "end_date": today,
        }
        response = client.get("/analytics/summary", params=params, headers=headers)
        assert response.status_code == 200


class TestMultipleUsers:
    """Проверка изоляции данных между пользователями."""

    def test_user_data_isolation(self, client):
        """Проверяет, что пользователи видят только свои данные."""
        # Создаем первого пользователя
        user1_data = {
            "name": "Пользователь 1",
            "login": "user1",
            "password": "pass1",
        }
        response = client.post("/users/register", json=user1_data)
        assert response.status_code == 200
        user1_result = response.json()
        user1_id = user1_result["id"]

        login1 = {"login": "user1", "password": "pass1"}
        response = client.post("/users/login", json=login1)
        token1 = response.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        # Создаем заметку первого пользователя
        note1 = {"orig_text": "Заметка пользователя 1. Здесь должно быть не менее пятидесяти символов для теста."}
        response = client.post("/notes/", json=note1, headers=headers1)
        assert response.status_code == 200
        note1_id = response.json()["id"]

        # Создаем второго пользователя
        user2_data = {
            "name": "Пользователь 2",
            "login": "user2",
            "password": "pass2",
        }
        response = client.post("/users/register", json=user2_data)
        assert response.status_code == 200
        user2_result = response.json()
        user2_id = user2_result["id"]

        login2 = {"login": "user2", "password": "pass2"}
        response = client.post("/users/login", json=login2)
        token2 = response.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Второй пользователь не может видеть заметку первого
        response = client.get(f"/notes/{note1_id}", headers=headers2)
        assert response.status_code == 404

        # Создаем заметку второго пользователя
        note2 = {"orig_text": "Заметка пользователя 2. Здесь должно быть не менее пятидесяти символов для теста."}
        response = client.post("/notes/", json=note2, headers=headers2)
        assert response.status_code == 200
        note2_id = response.json()["id"]

        # Первый пользователь не может видеть заметку второго
        response = client.get(f"/notes/{note2_id}", headers=headers1)
        assert response.status_code == 404


class TestAnalyticsIntegration:
    """Интеграционные тесты аналитики."""

    def test_analytics_with_seed_data(self, client):
        """Проверяет аналитику с тестовыми данными из seed."""
        # Логинимся как Даниил (из seed)
        login_data = {
            "login": "daniil",
            "password": "password",
        }
        response = client.post("/users/login", json=login_data)
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            today = "2024-12-31"
            params = {
                "start_date": "2024-01-01",
                "end_date": today,
            }

            # Получаем аналитику
            response = client.get("/analytics/summary", params=params, headers=headers)
            assert response.status_code == 200

            data = response.json()
            assert "average_mood_index" in data


class TestErrorResponseFormat:
    """Проверка формата ошибок в ответах."""

    def test_error_response_format(self, client):
        """Проверяет, что ошибки возвращаются в правильном формате."""
        # Неверный токен
        response = client.get("/users/me", headers={"Authorization": "Bearer invalid"})
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
        
        # Пустой запрос
        response = client.post("/users/register", json={})
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data
