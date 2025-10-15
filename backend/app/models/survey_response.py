"""
SurveyResponse model for storing survey responses and text analysis results.

This model captures user responses to survey questions along with OpenAI-powered
text quality analysis results including quality scores and flag reasons.
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Integer, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base

class SurveyResponse(Base):
    """Model for storing survey responses and text analysis results."""
    
    __tablename__ = "survey_responses"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    question_id = Column(String(36), ForeignKey("survey_questions.id"), nullable=False)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    
    # Response data
    response_text = Column(Text, nullable=False)
    response_time_ms = Column(Integer, nullable=True)  # Time to respond in milliseconds
    
    # Text analysis results (stored as JSON)
    text_analysis_result = Column(JSON, nullable=True)
    
    # Quality metrics
    quality_score = Column(Float, nullable=True)  # 0-100 quality score
    is_flagged = Column(Boolean, default=False)
    flag_reasons = Column(JSON, nullable=True)  # List of flag reasons
    
    # Analysis details
    gibberish_score = Column(Float, nullable=True)  # 0-1 gibberish probability
    copy_paste_score = Column(Float, nullable=True)  # 0-1 copy-paste probability
    relevance_score = Column(Float, nullable=True)  # 0-1 relevance score
    generic_score = Column(Float, nullable=True)  # 0-1 generic answer probability
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    analyzed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    survey_question = relationship("SurveyQuestion", back_populates="survey_response")
    session = relationship("Session", back_populates="survey_responses")
    
    def __repr__(self):
        return f"<SurveyResponse(id={self.id}, question={self.question_id}, quality={self.quality_score})>"
    
    @property
    def is_high_quality(self) -> bool:
        """Check if response is high quality (score >= 70)."""
        return self.quality_score is not None and self.quality_score >= 70
    
    @property
    def is_low_quality(self) -> bool:
        """Check if response is low quality (score < 30)."""
        return self.quality_score is not None and self.quality_score < 30
    
    @property
    def needs_review(self) -> bool:
        """Check if response needs manual review."""
        return self.is_flagged or (self.quality_score is not None and self.quality_score < 50)
    
    @property
    def truncated_response_text(self) -> str:
        """Get truncated response text for display."""
        if len(self.response_text) > 200:
            return self.response_text[:197] + "..."
        return self.response_text
    
    def get_flag_summary(self) -> str:
        """Get human-readable summary of flag reasons."""
        if not self.flag_reasons:
            return "No flags"
        
        flags = []
        for reason, details in self.flag_reasons.items():
            if isinstance(details, dict) and details.get('confidence', 0) > 0.5:
                flags.append(reason.replace('_', ' ').title())
        
        return ", ".join(flags) if flags else "No significant flags"
