from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.recommendation import RecommendationModel
from app.schemas.recommendation import RecommendationCreate


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
    mood_type: str | None,
    db: Session,
) -> list[RecommendationModel]:
    query = db.query(RecommendationModel)

    if mood_type is not None:
        allowed_mood_types = {"positive", "negative"}

        if mood_type not in allowed_mood_types:
            raise HTTPException(
                status_code=400,
                detail="mood_type должен быть positive или negative",
            )

        query = query.filter(RecommendationModel.mood_type == mood_type)

    return query.all()
