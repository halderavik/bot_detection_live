"""
GridResponse model for storing grid/matrix question responses and analysis results.

This model captures responses to grid questions along with analysis results
including straight-lining detection, pattern detection, variance scoring, and
satisficing behavior scoring.
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base

class GridResponse(Base):
    """Model for storing grid question responses and analysis results."""
    
    __tablename__ = "grid_responses"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Hierarchical fields (denormalized for efficient querying)
    survey_id = Column(String(255), nullable=True, index=True)
    platform_id = Column(String(255), nullable=True, index=True)
    respondent_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    
    # Foreign keys
    question_id = Column(String(36), ForeignKey("survey_questions.id"), nullable=False)
    
    # Grid-specific fields
    row_id = Column(String(255), nullable=True)  # Row identifier within the grid question
    column_id = Column(String(255), nullable=True)  # Column identifier within the grid question
    response_value = Column(Text, nullable=True)  # The actual response value
    response_time_ms = Column(Integer, nullable=True)  # Time to respond in milliseconds
    
    # Analysis fields
    is_straight_lined = Column(Boolean, default=False)  # Whether this response is part of a straight-lining pattern
    pattern_type = Column(String(50), nullable=True)  # Pattern detected: 'diagonal', 'reverse_diagonal', 'zigzag', 'straight_line', etc.
    variance_score = Column(Float, nullable=True)  # Variance score (0-1 scale)
    satisficing_score = Column(Float, nullable=True)  # Satisficing behavior score (0-1 scale)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    analyzed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    survey_question = relationship("SurveyQuestion", back_populates="grid_responses")
    session = relationship("Session", back_populates="grid_responses")
    
    def __repr__(self):
        return f"<GridResponse(id={self.id}, question={self.question_id}, pattern={self.pattern_type})>"
    
    @property
    def has_pattern(self) -> bool:
        """Check if a pattern was detected."""
        return self.pattern_type is not None
    
    @property
    def is_satisficing(self) -> bool:
        """Check if response shows satisficing behavior (score >= 0.7)."""
        return self.satisficing_score is not None and self.satisficing_score >= 0.7
    
    @property
    def has_low_variance(self) -> bool:
        """Check if response has low variance (score < 0.3)."""
        return self.variance_score is not None and self.variance_score < 0.3
    
    def get_pattern_description(self) -> str:
        """Get human-readable pattern description."""
        if not self.pattern_type:
            return "No pattern detected"
        
        pattern_descriptions = {
            "diagonal": "Diagonal pattern (1,2,3,4...)",
            "reverse_diagonal": "Reverse diagonal pattern",
            "zigzag": "Zigzag pattern",
            "straight_line": "Straight-lining pattern",
            "random": "Random pattern"
        }
        
        return pattern_descriptions.get(self.pattern_type, self.pattern_type.replace('_', ' ').title())
