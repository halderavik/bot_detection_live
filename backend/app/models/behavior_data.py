"""
BehaviorData model for storing user interaction events.

This model captures various types of user behavior events including
keystrokes, mouse movements, scroll events, and focus changes.
"""

from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Integer, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base

class BehaviorData(Base):
    """Model for storing user behavior events."""
    
    __tablename__ = "behavior_data"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to session
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    
    # Event metadata
    event_type = Column(String(50), nullable=False)  # 'keystroke', 'mouse', 'scroll', 'focus', etc.
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Event data (stored as JSON for flexibility)
    event_data = Column(JSON, nullable=False)
    
    # Element information
    element_id = Column(String(255), nullable=True)
    element_type = Column(String(50), nullable=True)
    element_class = Column(String(255), nullable=True)
    
    # Page context
    page_url = Column(Text, nullable=True)
    page_title = Column(Text, nullable=True)
    
    # Device information
    screen_width = Column(Integer, nullable=True)
    screen_height = Column(Integer, nullable=True)
    viewport_width = Column(Integer, nullable=True)
    viewport_height = Column(Integer, nullable=True)
    
    # Performance metrics
    load_time = Column(Float, nullable=True)  # Page load time in milliseconds
    response_time = Column(Float, nullable=True)  # Event response time
    
    # Relationships
    session = relationship("Session", back_populates="behavior_data")
    
    def __repr__(self):
        return f"<BehaviorData(id={self.id}, type={self.event_type}, session={self.session_id})>"
    
    @property
    def is_keystroke_event(self) -> bool:
        """Check if this is a keystroke event."""
        return self.event_type == "keystroke"
    
    @property
    def is_mouse_event(self) -> bool:
        """Check if this is a mouse event."""
        return self.event_type in ["mouse_move", "mouse_click", "mouse_drag"]
    
    @property
    def is_scroll_event(self) -> bool:
        """Check if this is a scroll event."""
        return self.event_type == "scroll"
    
    @property
    def is_focus_event(self) -> bool:
        """Check if this is a focus/blur event."""
        return self.event_type in ["focus", "blur"] 