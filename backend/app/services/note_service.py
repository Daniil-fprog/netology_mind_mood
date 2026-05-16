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
