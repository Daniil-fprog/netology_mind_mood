import uuid

from sqlalchemy.orm import Session

from app.models.user import UserModel


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
