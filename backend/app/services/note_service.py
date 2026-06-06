from datetime import datetime
from typing import Optional, List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.note import NoteModel
from app.models.user import UserModel
from app.schemas.note import NoteCreate, NoteUpdate


def create_note_service(
    note_data: NoteCreate,
    current_user: UserModel,
    db: Session,
) -> NoteModel:
    db_note = NoteModel(
        user_id=current_user.id,
        orig_text=note_data.orig_text,
    )

    db.add(db_note)
    db.commit()
    db.refresh(db_note)

    return db_note


def get_current_user_notes_service(
    current_user: UserModel,
    db: Session,
) -> list[NoteModel]:
    return db.query(NoteModel).filter(NoteModel.user_id == current_user.id).all()


def get_current_user_note_by_id_service(
    note_id: int,
    current_user: UserModel,
    db: Session,
) -> tuple[NoteModel, List[dict]]:
    note = (
        db.query(NoteModel)
        # .options(joinedload(NoteModel.recommendations))
        .filter(
            NoteModel.id == note_id,
            NoteModel.user_id == current_user.id,
        )
        .first()
    )

    if note is None:
        raise HTTPException(
            status_code=404,
            detail="Запись не найдена",
        )
    
    return note



def update_note_service(
    note_id: int,
    note_data: NoteUpdate,
    current_user: UserModel,
    db: Session,
) -> NoteModel:
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
        note.sentiment_label = None
        note.sentiment_score = None

    db.commit()
    db.refresh(note)

    return note


def filter_notes_service(
    current_user: UserModel,
    db: Session,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sentiment_label: Optional[str] = None,
    sort: str = "newest",
) -> list[NoteModel]:
    query = db.query(NoteModel).filter(NoteModel.user_id == current_user.id)

    # Поиск по тексту
    if search:
        query = query.filter(NoteModel.orig_text.ilike(f"%{search}%"))

    # Фильтрация по дате от
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(NoteModel.created_at >= date_from_obj)
        except ValueError:
            pass

    # Фильтрация по дате до
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
            query = query.filter(NoteModel.created_at <= date_to_obj)
        except ValueError:
            pass

    # Фильтрация по sentiment_label
    if sentiment_label:
        query = query.filter(NoteModel.sentiment_label == sentiment_label)

    # Cортировка по дате (новый, старый)
    if sort:
        if sort == "newest":
            query = query.order_by(NoteModel.created_at.desc())
        elif sort == "oldest":
            query = query.order_by(NoteModel.created_at.asc())
        else:
            query = query.order_by(NoteModel.created_at.desc())

    return query.all()
