"""
Session model for tracking user sessions.

This model represents a user session with metadata and tracking information.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship

from database.database import Base


class Session(Base):
    """Session model for tracking user interactions."""
    
    __tablename__ = "sessions"
    
    # Primary key
    id = Column(String(36), primary_key=True, index=True)
    
    # Session metadata
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    referrer = Column(Text, nullable=True)
    
    # Session state
    is_active = Column(Boolean, default=True)
    is_bot = Column(Boolean, nullable=True)  # Final classification result
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    behavior_data = relationship("BehaviorData", back_populates="session", cascade="all, delete-orphan")
    detection_results = relationship("DetectionResult", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        """String representation of the session."""
        return f"<Session(id={self.id}, is_bot={self.is_bot}, is_active={self.is_active})>"
    
    def update_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert session to dictionary."""
        return {
            "id": self.id,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "referrer": self.referrer,
            "is_active": self.is_active,
            "is_bot": self.is_bot,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
        } 