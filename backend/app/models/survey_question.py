"""
SurveyQuestion model for storing survey question metadata.

This model captures question information including text, type, element details,
and timing for text quality analysis.
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base

class SurveyQuestion(Base):
    """Model for storing survey question metadata."""
    
    __tablename__ = "survey_questions"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to session
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    
    # Question metadata
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=True)  # 'open_ended', 'multiple_choice', etc.
    element_id = Column(String(255), nullable=True)  # HTML element ID
    element_type = Column(String(50), nullable=True)  # 'textarea', 'input', etc.
    page_url = Column(Text, nullable=True)
    page_title = Column(Text, nullable=True)
    
    # Timing
    asked_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("Session", back_populates="survey_questions")
    survey_response = relationship("SurveyResponse", back_populates="survey_question", uselist=False)
    grid_responses = relationship("GridResponse", back_populates="survey_question", cascade="all, delete-orphan")
    timing_analyses = relationship("TimingAnalysis", back_populates="survey_question", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SurveyQuestion(id={self.id}, session={self.session_id}, type={self.question_type})>"
    
    @property
    def is_open_ended(self) -> bool:
        """Check if this is an open-ended question."""
        return self.question_type in ["open_ended", "text", "textarea"] or \
               self.element_type in ["textarea", "input"]
    
    @property
    def truncated_question_text(self) -> str:
        """Get truncated question text for display."""
        if len(self.question_text) > 100:
            return self.question_text[:97] + "..."
        return self.question_text
