"""
Quality rules saved for one survey id.

A survey without a row uses the recommended defaults. The rules decide how the live
quality dashboard, its CSV export, and the LQ_ variables added to a data file judge
each respondent; they do not change what the detection service stores.
"""

from sqlalchemy import JSON, Column, DateTime, String
from sqlalchemy.sql import func

from app.database import Base


class SurveyQualityRules(Base):
    """The rules one survey uses, stored as the full rules object."""

    __tablename__ = "survey_quality_rules"

    survey_id = Column(String(255), primary_key=True)
    rules = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
