from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.user import UserModel
from app.schemas.recommendation import RecommendationCreate, RecommendationOut
from app.services.recommendation_service import (
    create_recommendation_service,
    get_recommendations_service,
)


router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/", response_model=RecommendationOut)
def create_recommendation(
    recommendation_data: RecommendationCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return create_recommendation_service(recommendation_data, db)


@router.get("/", response_model=list[RecommendationOut])
def get_recommendations(
    db: Session = Depends(get_db),
    mood_type: Optional[str] = None,
    current_user: UserModel = Depends(get_current_user),
):
    return get_recommendations_service(db, mood_type)