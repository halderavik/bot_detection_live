"""
Detection result model for storing bot detection analysis results.

This model stores the results of bot detection analysis including scores,
confidence levels, and processing metrics.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, Text, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship

from database.database import Base


class DetectionResult(Base):
    """Detection result model for storing bot detection analysis results."""
    
    __tablename__ = "detection_results"
    
    # Primary key
    id = Column(String(36), primary_key=True, index=True)
    
    # Foreign key to session
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    
    # Detection results
    bot_score = Column(Float, nullable=False)  # 0.0 to 1.0, higher = more likely bot
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0, confidence in the result
    is_bot = Column(Boolean, nullable=False)  # Final classification
    
    # Detailed analysis (stored as JSON)
    analysis_details = Column(JSON, nullable=True)
    
    # Performance metrics
    processing_time_ms = Column(Float, nullable=False)
    event_count = Column(Integer, nullable=False, default=0)
    
    # Detection metadata
    detection_method = Column(String(50), nullable=False, default="rule_based")
    model_version = Column(String(20), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="detection_results")
    
    def __repr__(self):
        """String representation of the detection result."""
        return f"<DetectionResult(id={self.id}, bot_score={self.bot_score}, is_bot={self.is_bot})>"
    
    def to_dict(self):
        """Convert detection result to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "bot_score": self.bot_score,
            "confidence": self.confidence,
            "is_bot": self.is_bot,
            "analysis_details": self.analysis_details,
            "processing_time_ms": self.processing_time_ms,
            "event_count": self.event_count,
            "detection_method": self.detection_method,
            "model_version": self.model_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def create_result(cls, session_id: str, bot_score: float, confidence: float,
                     is_bot: bool, processing_time_ms: float, event_count: int,
                     analysis_details: dict = None, detection_method: str = "rule_based",
                     model_version: str = None):
        """Create a new detection result."""
        return cls(
            session_id=session_id,
            bot_score=bot_score,
            confidence=confidence,
            is_bot=is_bot,
            analysis_details=analysis_details or {},
            processing_time_ms=processing_time_ms,
            event_count=event_count,
            detection_method=detection_method,
            model_version=model_version
        )
    
    def get_risk_level(self) -> str:
        """Get risk level based on bot score."""
        if self.bot_score >= 0.8:
            return "high"
        elif self.bot_score >= 0.6:
            return "medium"
        elif self.bot_score >= 0.4:
            return "low"
        else:
            return "very_low"
    
    def get_confidence_level(self) -> str:
        """Get confidence level description."""
        if self.confidence >= 0.9:
            return "very_high"
        elif self.confidence >= 0.7:
            return "high"
        elif self.confidence >= 0.5:
            return "medium"
        else:
            return "low" 