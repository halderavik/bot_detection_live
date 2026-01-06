"""
Session model for tracking user sessions.

This model stores session metadata including user agent, IP address,
timestamps, and session status for bot detection analysis.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base

class Session(Base):
    """Session model for tracking user interactions."""
    
    __tablename__ = "sessions"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Session metadata
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    referrer = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Session status
    is_active = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    
    # Integration metadata
    survey_id = Column(String(255), nullable=True, index=True)
    respondent_id = Column(String(255), nullable=True, index=True)
    platform = Column(String(50), nullable=True)  # 'qualtrics', 'decipher', etc. (kept for backward compatibility)
    platform_id = Column(String(255), nullable=True, index=True)  # Platform identifier for hierarchical structure
    
    # Device fingerprinting (computed)
    device_fingerprint = Column(Text, nullable=True)
    
    # Relationships
    behavior_data = relationship("BehaviorData", back_populates="session", cascade="all, delete-orphan")
    detection_results = relationship("DetectionResult", back_populates="session", cascade="all, delete-orphan")
    survey_questions = relationship("SurveyQuestion", back_populates="session", cascade="all, delete-orphan")
    survey_responses = relationship("SurveyResponse", back_populates="session", cascade="all, delete-orphan")
    fraud_indicators = relationship("FraudIndicator", back_populates="session", cascade="all, delete-orphan")
    
    # Composite indexes for efficient hierarchical queries
    __table_args__ = (
        Index('idx_survey_platform_respondent_session', 'survey_id', 'platform_id', 'respondent_id', 'id'),
        Index('idx_survey_platform', 'survey_id', 'platform_id'),
        Index('idx_survey_platform_respondent', 'survey_id', 'platform_id', 'respondent_id'),
        Index('idx_session_fingerprint', 'device_fingerprint'),
    )
    
    def __repr__(self):
        return f"<Session(id={self.id}, platform_id={self.platform_id}, is_active={self.is_active})>"
    
    @property
    def event_count(self) -> int:
        """Get the total number of events for this session."""
        return len(self.behavior_data) if self.behavior_data else 0
    
    # Remove the latest_detection property as it causes async issues
    # The controller will handle getting the latest detection result 