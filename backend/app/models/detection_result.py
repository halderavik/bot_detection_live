"""
DetectionResult model for storing bot detection analysis results.

This model stores the results of bot detection analysis including
confidence scores, detection methods used, and processing metrics.
"""

from sqlalchemy import Column, String, DateTime, Float, Boolean, JSON, ForeignKey, Text, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base

class DetectionResult(Base):
    """Model for storing bot detection analysis results."""
    
    __tablename__ = "detection_results"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to session
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    
    # Detection results
    is_bot = Column(Boolean, nullable=False)
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    risk_level = Column(String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    
    # Detection methods used
    detection_methods = Column(JSON, nullable=False)  # List of methods used
    method_scores = Column(JSON, nullable=False)  # Individual method scores
    
    # Processing metrics
    processing_time_ms = Column(Float, nullable=False)  # Time taken for analysis
    event_count = Column(Integer, nullable=False)  # Number of events analyzed
    
    # Analysis details
    analysis_summary = Column(Text, nullable=True)  # Human-readable summary
    flagged_patterns = Column(JSON, nullable=True)  # Specific patterns that triggered detection
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("Session", back_populates="detection_results")
    
    def __repr__(self):
        return f"<DetectionResult(id={self.id}, is_bot={self.is_bot}, confidence={self.confidence_score})>"
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if the detection has high confidence (>0.8)."""
        return self.confidence_score > 0.8
    
    @property
    def is_medium_confidence(self) -> bool:
        """Check if the detection has medium confidence (0.5-0.8)."""
        return 0.5 <= self.confidence_score <= 0.8
    
    @property
    def is_low_confidence(self) -> bool:
        """Check if the detection has low confidence (<0.5)."""
        return self.confidence_score < 0.5
    
    @property
    def risk_score(self) -> float:
        """Calculate risk score based on confidence and bot probability."""
        if self.is_bot:
            return self.confidence_score
        else:
            return 1.0 - self.confidence_score
    
    def get_method_score(self, method_name: str) -> float:
        """Get the score for a specific detection method."""
        if self.method_scores and method_name in self.method_scores:
            return self.method_scores[method_name]
        return 0.0
    
    def get_flagged_patterns_summary(self) -> str:
        """Get a human-readable summary of flagged patterns."""
        if not self.flagged_patterns:
            return "No specific patterns flagged"
        
        patterns = []
        for pattern_type, details in self.flagged_patterns.items():
            if isinstance(details, dict):
                count = details.get('count', 0)
                severity = details.get('severity', 'unknown')
                patterns.append(f"{pattern_type}: {count} events ({severity} severity)")
            else:
                patterns.append(f"{pattern_type}: {details}")
        
        return "; ".join(patterns) 