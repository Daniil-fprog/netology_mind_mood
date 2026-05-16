from app.db.database import SessionLocal
from app.models.note import NoteModel
from app.services.sentiment_service import predict_sentimental
from app.services.translation_service import translate_to_english


def translate_note_background(note_id: int):
    db = SessionLocal()

    try:
        note = db.query(NoteModel).filter(NoteModel.id == note_id).first()

        if note is None:
            print("Заметка не найдена")
            return

        try:
            translated_text = translate_to_english(note.orig_text)

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