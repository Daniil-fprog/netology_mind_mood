from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.db.database import Base


class RecommendationModel(Base):
    __tablename__ = "recommendation"

    id = Column(Integer, primary_key=True, index=True)

    rec_name = Column(String, nullable=False)
    rec_text = Column(String, nullable=False)
    mood_type = Column(String, nullable=False)  # positive / negative

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
