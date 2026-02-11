"""
TimingAnalysis model for storing per-question timing analysis results.

This model captures timing analysis for survey questions including speeder
detection (too fast), flatliner detection (too slow), and statistical anomaly
detection.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base

class TimingAnalysis(Base):
    """Model for storing per-question timing analysis results."""
    
    __tablename__ = "timing_analysis"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Hierarchical fields (denormalized for efficient querying)
    survey_id = Column(String(255), nullable=True, index=True)
    platform_id = Column(String(255), nullable=True, index=True)
    respondent_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    
    # Foreign keys
    question_id = Column(String(36), ForeignKey("survey_questions.id"), nullable=False)
    
    # Timing fields
    question_time_ms = Column(Integer, nullable=False)  # Time taken to answer this question
    is_speeder = Column(Boolean, default=False)  # Response time < threshold (too fast)
    is_flatliner = Column(Boolean, default=False)  # Response time > threshold (too slow)
    threshold_used = Column(Float, nullable=True)  # Threshold used for detection (in ms)
    
    # Anomaly fields
    anomaly_score = Column(Float, nullable=True)  # Statistical anomaly score (z-score)
    anomaly_type = Column(String(50), nullable=True)  # Type of anomaly: 'speeder', 'flatliner', 'outlier', etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    analyzed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    survey_question = relationship("SurveyQuestion", back_populates="timing_analyses")
    session = relationship("Session", back_populates="timing_analyses")
    
    def __repr__(self):
        return f"<TimingAnalysis(id={self.id}, question={self.question_id}, time={self.question_time_ms}ms)>"
    
    @property
    def is_anomaly(self) -> bool:
        """Check if timing is anomalous (z-score > 2.5)."""
        return self.anomaly_score is not None and abs(self.anomaly_score) > 2.5
    
    @property
    def needs_review(self) -> bool:
        """Check if timing analysis needs manual review."""
        return self.is_speeder or self.is_flatliner or self.is_anomaly
    
    @property
    def time_in_seconds(self) -> float:
        """Get response time in seconds."""
        return self.question_time_ms / 1000.0 if self.question_time_ms else 0.0
    
    def get_anomaly_description(self) -> str:
        """Get human-readable anomaly description."""
        if not self.is_anomaly and not self.is_speeder and not self.is_flatliner:
            return "Normal timing"
        
        descriptions = []
        if self.is_speeder:
            descriptions.append("Speeder (too fast)")
        if self.is_flatliner:
            descriptions.append("Flatliner (too slow)")
        if self.is_anomaly:
            descriptions.append(f"Statistical outlier (z-score: {self.anomaly_score:.2f})")
        
        return ", ".join(descriptions) if descriptions else "Normal timing"
