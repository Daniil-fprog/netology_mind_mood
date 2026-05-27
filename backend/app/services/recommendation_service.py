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
    allowed_mood_types = {"positive", "negative"}

    if recommendation_data.mood_type not in allowed_mood_types:
        raise HTTPException(
            status_code=400,
            detail="mood_type должен быть positive или negative",
        )

    db_recommendation = RecommendationModel(
        rec_name=recommendation_data.rec_name,
        rec_text=recommendation_data.rec_text,
        mood_type=recommendation_data.mood_type,
    )

    db.add(db_recommendation)
    db.commit()
    db.refresh(db_recommendation)

    return db_recommendation


def get_recommendations_service(
    sentiment_score: int | None,
    db: Session,
    limit: int = 2,
) -> list[RecommendationModel]:
    query = db.query(RecommendationModel)

    if sentiment_score is not None:
        if sentiment_score > 100 | sentiment_score < 0:
            raise HTTPException(
                status_code=400,
                detail="mood_type должен быть positive или negative",
            )

        query = query.filter(
            RecommendationModel.score_from <= sentiment_score,
            RecommendationModel.score_to >= sentiment_score,
        ).limit(limit)

    return query.all()
