"""
Behavior data model for storing user interaction events.

This model captures various types of user interactions for bot detection analysis.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from database.database import Base


class BehaviorData(Base):
    """Behavior data model for storing user interaction events."""
    
    __tablename__ = "behavior_data"
    
    # Primary key
    id = Column(String(36), primary_key=True, index=True)
    
    # Foreign key to session
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    
    # Event metadata
    event_type = Column(String(50), nullable=False)  # keystroke, mouse, scroll, focus, etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Event data (stored as JSON for flexibility)
    event_data = Column(JSON, nullable=False)
    
    # Additional metadata
    page_url = Column(Text, nullable=True)
    element_id = Column(String(255), nullable=True)
    element_type = Column(String(50), nullable=True)
    
    # Performance metrics
    processing_time_ms = Column(Float, nullable=True)
    
    # Relationships
    session = relationship("Session", back_populates="behavior_data")
    
    def __repr__(self):
        """String representation of the behavior data."""
        return f"<BehaviorData(id={self.id}, event_type={self.event_type}, session_id={self.session_id})>"
    
    def to_dict(self):
        """Convert behavior data to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "event_data": self.event_data,
            "page_url": self.page_url,
            "element_id": self.element_id,
            "element_type": self.element_type,
            "processing_time_ms": self.processing_time_ms,
        }
    
    @classmethod
    def create_keystroke_event(cls, session_id: str, key_code: int, key_char: str, 
                              timestamp: float, page_url: str = None, element_id: str = None):
        """Create a keystroke event."""
        return cls(
            session_id=session_id,
            event_type="keystroke",
            event_data={
                "key_code": key_code,
                "key_char": key_char,
                "timestamp": timestamp
            },
            page_url=page_url,
            element_id=element_id,
            element_type="input"
        )
    
    @classmethod
    def create_mouse_event(cls, session_id: str, event_type: str, x: int, y: int,
                          button: int = None, timestamp: float = None, page_url: str = None):
        """Create a mouse event (click, move, etc.)."""
        return cls(
            session_id=session_id,
            event_type=f"mouse_{event_type}",
            event_data={
                "x": x,
                "y": y,
                "button": button,
                "timestamp": timestamp or datetime.utcnow().timestamp()
            },
            page_url=page_url
        )
    
    @classmethod
    def create_scroll_event(cls, session_id: str, scroll_x: int, scroll_y: int,
                           timestamp: float = None, page_url: str = None):
        """Create a scroll event."""
        return cls(
            session_id=session_id,
            event_type="scroll",
            event_data={
                "scroll_x": scroll_x,
                "scroll_y": scroll_y,
                "timestamp": timestamp or datetime.utcnow().timestamp()
            },
            page_url=page_url
        )
    
    @classmethod
    def create_focus_event(cls, session_id: str, event_type: str, element_id: str = None,
                          timestamp: float = None, page_url: str = None):
        """Create a focus/blur event."""
        return cls(
            session_id=session_id,
            event_type=f"focus_{event_type}",
            event_data={
                "element_id": element_id,
                "timestamp": timestamp or datetime.utcnow().timestamp()
            },
            page_url=page_url,
            element_id=element_id
        ) 