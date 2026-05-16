from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import UserModel
from app.schemas.user import UserCreate, UserLogin
from app.utils.login_generator import generate_login


def register_user_service(user_data: UserCreate, db: Session) -> UserModel:
    if user_data.phone:
        existing_phone = (
            db.query(UserModel)
            .filter(UserModel.phone == user_data.phone)
            .first()
        )

        if existing_phone:
            raise HTTPException(
                status_code=400,
                detail="Пользователь с таким телефоном уже существует",
            )

    generated_login = generate_login(db)

    db_user = UserModel(
        name=user_data.name,
        login=generated_login,
        password_hash=hash_password(user_data.password),
        phone=user_data.phone,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def authenticate_user_service(user_data: UserLogin, db: Session) -> UserModel:
    user = db.query(UserModel).filter(UserModel.login == user_data.login).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Неверный логин или пароль",
        )

    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Неверный логин или пароль",
        )

    return user