from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class NoteModel(Base):
    __tablename__ = "note"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    orig_text = Column(String, nullable=False)
    translate_text = Column(String, nullable=True)
    translate_status = Column(String, default="pending")

    sentiment_label = Column(String, nullable=True)
    sentiment_score = Column(Integer, nullable=True) # скор от 0 до 100
    model_confidence = Column(Integer, nullable=True) # скор от 0 до 100

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserModel", back_populates="notes")

    recommendations = relationship(
        "RecommendationModel",
        secondary="note_recommendation",
        back_populates="notes",
    )
