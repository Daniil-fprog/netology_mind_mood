from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import UserModel
from app.schemas.note import NoteCreate, NoteOut, NoteUpdate
from app.services.note_service import (
    create_note_service,
    get_current_user_notes_service,
    get_current_user_note_by_id_service,
    update_note_service,
)
from app.tasks.note_tasks import translate_note_background


router = APIRouter(prefix="/notes", tags=["Notes"])


@router.post("/", response_model=NoteOut)
def create_note(
    note_data: NoteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    note = create_note_service(note_data, current_user, db)

    background_tasks.add_task(translate_note_background, note.id)

    return note


@router.get("/", response_model=list[NoteOut])
def get_notes(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return get_current_user_notes_service(current_user, db)


@router.get("/{note_id}", response_model=NoteOut)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return get_current_user_note_by_id_service(note_id, current_user, db)


@router.patch("/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    note_data: NoteUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    note = update_note_service(note_id, note_data, current_user, db)

    background_tasks.add_task(translate_note_background, note.id)

    return note