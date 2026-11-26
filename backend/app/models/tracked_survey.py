"""
Surveys that had tracking added through the Decipher XML upload.

One row per tracking survey id. Uploading the same survey again updates the row,
so the id (and the dashboard its responses go to) stays the same.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class TrackedSurvey(Base):
    """A survey id that tracking was added to, with the options last used."""

    __tablename__ = "tracked_surveys"

    survey_id = Column(String(255), primary_key=True)
    title = Column(String(255), nullable=True)
    source_filename = Column(String(255), nullable=True)
    platform_id = Column(String(50), nullable=False, default="decipher")
    signed = Column(Boolean, nullable=False, default=False)
    terminate = Column(Boolean, nullable=False, default=False)
    privacy_notice = Column(Boolean, nullable=False, default=False)
    # Decipher survey the tracked XML was last uploaded to (selfserve/123/456789).
    decipher_path = Column(String(255), nullable=True)
    uploads = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
