from sqlalchemy import Column, ForeignKey, Integer

from app.db.database import Base


class NoteRecommendationModel(Base):
    __tablename__ = "note_recommendation"

    note_id = Column(
        Integer,
        ForeignKey("note.id", ondelete="CASCADE"),
        primary_key=True,
    )

    recommendation_id = Column(
        Integer,
        ForeignKey("recommendation.id", ondelete="CASCADE"),
        primary_key=True,
    )
