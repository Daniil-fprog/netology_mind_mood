from app.db.database import SessionLocal
from app.models.note import NoteModel
from app.services.sentiment_service import predict_sentimental
from app.services.translation_service import translate_to_english
from app.services.recommendation_service import attach_recommendations_to_note


def translate_note_background(note_id: int):
    db = SessionLocal()

    try:
        note = db.query(NoteModel).filter(NoteModel.id == note_id).first()

        if note is None:
            print("Заметка не найдена")
            return

        try:
            # 1. Начали обработку
            note.translate_status = "pending"
            db.commit()
            db.refresh(note)

            # 2. Перевод
            translated_text = translate_to_english(note.orig_text)

            note.translate_text = translated_text
            note.translate_status = "translated"
            db.commit()
            db.refresh(note)

            # 3. Получение скора
            sentiment_label, sentiment_score = predict_sentimental(translated_text)

            note.sentiment_label = sentiment_label
            note.sentiment_score = sentiment_score
            # note.model_confidence = model_confidence

            note.translate_status = "analyzed"
            db.commit()
            db.refresh(note)

            # 4. Прикрепление рекомендаций
            attach_recommendations_to_note(
                db=db,
                note=note,
                limit=2,
            )

            # 5. Полностью готово
            note.translate_status = "done"
            db.commit()
            db.refresh(note)

        except Exception as e:
            print("Ошибка перевода:", e)
            note.translate_status = "error"
            note.sentiment_label = "unknown"
            note.sentiment_score = 0

            db.commit()

    finally:
        db.close()
