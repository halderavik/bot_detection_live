"""
Surveys that require a signed tracking token.

A survey becomes protected the first time a session is created for it with a
valid token. From then on, sessions for that survey id need the token, so
nobody can add fake sessions under its name.
"""

from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from app.database import Base


class ProtectedSurvey(Base):
    """A survey id whose sessions must carry a valid tracking token."""

    __tablename__ = "protected_surveys"

    survey_id = Column(String(255), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
