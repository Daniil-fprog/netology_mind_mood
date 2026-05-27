from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class RecommendationModel(Base):
    __tablename__ = "recommendation"

    id = Column(Integer, primary_key=True, index=True)

    rec_name = Column(String, nullable=False)
    rec_text = Column(String, nullable=False)

    mood_type = Column(String, nullable=False)  # positive / negative

    # диапазон, для какого score подходит рекомендация
    score_from = Column(Integer, nullable=False)
    score_to = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    notes = relationship(
        "NoteModel",
        secondary="note_recommendation",
        back_populates="recommendations",
    )
