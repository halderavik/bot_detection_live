"""
Utility functions package.

This package contains helper functions and utilities for the bot detection system.
"""

from .logger import setup_logger
from .helpers import (
    generate_session_id, 
    validate_event_data, 
    calculate_confidence_score,
    determine_risk_level,
    sanitize_user_agent,
    is_valid_ip_address,
    format_processing_time
)

__all__ = [
    "setup_logger", 
    "generate_session_id", 
    "validate_event_data", 
    "calculate_confidence_score",
    "determine_risk_level",
    "sanitize_user_agent",
    "is_valid_ip_address",
    "format_processing_time"
] 