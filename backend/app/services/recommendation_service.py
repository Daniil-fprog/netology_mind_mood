from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.recommendation import RecommendationModel
from app.models.note import NoteModel

from app.schemas.recommendation import RecommendationCreate


def attach_recommendations_to_note(
    db: Session,
    note: NoteModel,
    limit: int = 2,
) -> NoteModel:
    """
    Подбирает рекомендации по sentiment_score записи
    и прикрепляет их к note.
    """

    if note.sentiment_score is None:
        return note

    recommendations = (
        db.query(RecommendationModel)
        .filter(
            RecommendationModel.score_from <= note.sentiment_score,
            RecommendationModel.score_to >= note.sentiment_score,
        )
        .limit(limit)
        .all()
    )

    note.recommendations = recommendations

    db.add(note)
    db.commit()
    db.refresh(note)

    return note


def create_recommendation_service(
    recommendation_data: RecommendationCreate,
    db: Session,
) -> RecommendationModel:
    allowed_mood_types = {"positive", "neutral", "negative"}

    if recommendation_data.mood_type not in allowed_mood_types:
        raise HTTPException(
            status_code=422,
            detail=f"mood_type должен быть одним из: {', '.join(allowed_mood_types)}",
        )

    db_recommendation = RecommendationModel(
        rec_name=recommendation_data.rec_name,
        rec_text=recommendation_data.rec_text,
        mood_type=recommendation_data.mood_type,
        score_from=recommendation_data.score_from,
        score_to=recommendation_data.score_to,
    )

    db.add(db_recommendation)
    db.commit()
    db.refresh(db_recommendation)

    return db_recommendation


def get_recommendations_service(
    db: Session,
    mood_type: str | None = None,
    limit: int = 2,
) -> list[RecommendationModel]:
    query = db.query(RecommendationModel)

    if mood_type is not None and mood_type.strip() != "":
        allowed_mood_types = {"positive", "neutral", "negative"}
        if mood_type not in allowed_mood_types:
            raise HTTPException(
                status_code=422,
                detail=f"mood_type должен быть одним из: {', '.join(allowed_mood_types)}",
            )
        query = query.filter(RecommendationModel.mood_type == mood_type).limit(limit)

    return query.all()
