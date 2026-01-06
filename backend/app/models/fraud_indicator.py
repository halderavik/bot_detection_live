"""
FraudIndicator model for storing fraud detection analysis results.

This model stores the results of fraud detection analysis including
IP tracking, device fingerprinting, duplicate response detection,
geolocation checks, and velocity monitoring.
"""

from sqlalchemy import Column, String, DateTime, Float, Boolean, JSON, ForeignKey, Text, Integer, Numeric, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base

class FraudIndicator(Base):
    """Model for storing fraud detection analysis results."""
    
    __tablename__ = "fraud_indicators"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to session
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    
    # Hierarchical fields (denormalized from sessions for efficient querying)
    survey_id = Column(String(255), nullable=True, index=True)
    platform_id = Column(String(255), nullable=True, index=True)
    respondent_id = Column(String(255), nullable=True, index=True)
    
    # IP Analysis
    ip_address = Column(String(45), nullable=True)
    ip_usage_count = Column(Integer, default=0)
    ip_sessions_today = Column(Integer, default=0)
    ip_risk_score = Column(Numeric(3, 2), nullable=True)
    ip_country_code = Column(String(2), nullable=True)
    ip_city = Column(String(100), nullable=True)
    
    # Device Fingerprint
    device_fingerprint = Column(Text, nullable=True)
    fingerprint_usage_count = Column(Integer, default=0)
    fingerprint_risk_score = Column(Numeric(3, 2), nullable=True)
    
    # Response Pattern
    response_similarity_score = Column(Numeric(3, 2), nullable=True)
    duplicate_response_count = Column(Integer, default=0)
    
    # Geolocation
    geolocation_consistent = Column(Boolean, default=True)
    geolocation_risk_score = Column(Numeric(3, 2), nullable=True)
    
    # Velocity
    responses_per_hour = Column(Numeric(5, 2), nullable=True)
    velocity_risk_score = Column(Numeric(3, 2), nullable=True)
    
    # Overall
    overall_fraud_score = Column(Numeric(3, 2), nullable=True)
    is_duplicate = Column(Boolean, default=False)
    fraud_confidence = Column(Numeric(3, 2), nullable=True)
    
    # Metadata
    flag_reasons = Column(JSON, nullable=True)
    analysis_details = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("Session", back_populates="fraud_indicators")
    
    # Indexes
    __table_args__ = (
        Index('idx_fraud_ip', 'ip_address'),
        Index('idx_fraud_fingerprint', 'device_fingerprint'),
        Index('idx_fraud_session', 'session_id'),
        Index('idx_fraud_created_at', 'created_at'),
        Index('idx_fraud_survey', 'survey_id'),
        Index('idx_fraud_survey_platform', 'survey_id', 'platform_id'),
        Index('idx_fraud_survey_platform_respondent', 'survey_id', 'platform_id', 'respondent_id'),
        Index('idx_fraud_survey_platform_respondent_session', 'survey_id', 'platform_id', 'respondent_id', 'session_id'),
    )
    
    def __repr__(self):
        return f"<FraudIndicator(id={self.id}, session_id={self.session_id}, fraud_score={self.overall_fraud_score})>"
    
    @property
    def is_high_risk(self) -> bool:
        """Check if the fraud indicator has high risk (>0.7)."""
        if self.overall_fraud_score is None:
            return False
        return float(self.overall_fraud_score) > 0.7
    
    @property
    def is_medium_risk(self) -> bool:
        """Check if the fraud indicator has medium risk (0.4-0.7)."""
        if self.overall_fraud_score is None:
            return False
        score = float(self.overall_fraud_score)
        return 0.4 <= score <= 0.7
    
    @property
    def is_low_risk(self) -> bool:
        """Check if the fraud indicator has low risk (<0.4)."""
        if self.overall_fraud_score is None:
            return True
        return float(self.overall_fraud_score) < 0.4
    
    @property
    def risk_level(self) -> str:
        """Get risk level based on overall fraud score."""
        if self.overall_fraud_score is None:
            return "LOW"
        
        score = float(self.overall_fraud_score)
        if score >= 0.9:
            return "CRITICAL"
        elif score >= 0.7:
            return "HIGH"
        elif score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_flag_reasons_summary(self) -> str:
        """Get a human-readable summary of flag reasons."""
        if not self.flag_reasons:
            return "No specific fraud indicators"
        
        reasons = []
        for reason_type, details in self.flag_reasons.items():
            if isinstance(details, dict):
                count = details.get('count', 0)
                severity = details.get('severity', 'unknown')
                reasons.append(f"{reason_type}: {count} occurrences ({severity} severity)")
            else:
                reasons.append(f"{reason_type}: {details}")
        
        return "; ".join(reasons)
