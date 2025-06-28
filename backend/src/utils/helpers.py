"""
Helper utilities for the Bot Detection API.

This module contains common utility functions used across the application.
"""

import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid.uuid4())


def generate_event_id() -> str:
    """Generate a unique event ID."""
    return str(uuid.uuid4())


def get_current_timestamp() -> float:
    """Get current timestamp in seconds."""
    return time.time()


def format_timestamp(timestamp: float) -> str:
    """Format timestamp to ISO string."""
    return datetime.fromtimestamp(timestamp).isoformat()


def calculate_processing_time(start_time: float) -> float:
    """Calculate processing time in milliseconds."""
    return (time.time() - start_time) * 1000


def validate_event_data(event_data: Dict[str, Any]) -> bool:
    """Validate event data structure."""
    required_fields = ["event_type", "timestamp"]
    
    for field in required_fields:
        if field not in event_data:
            return False
    
    # Validate timestamp
    if not isinstance(event_data["timestamp"], (int, float)):
        return False
    
    # Validate event_type
    if not isinstance(event_data["event_type"], str):
        return False
    
    return True


def sanitize_user_agent(user_agent: str) -> str:
    """Sanitize user agent string."""
    if not user_agent:
        return "Unknown"
    
    # Remove potentially sensitive information
    sensitive_patterns = [
        "password", "token", "key", "secret", "auth"
    ]
    
    sanitized = user_agent.lower()
    for pattern in sensitive_patterns:
        if pattern in sanitized:
            return "Sanitized"
    
    return user_agent[:500]  # Limit length


def extract_ip_from_headers(headers: Dict[str, str]) -> Optional[str]:
    """Extract real IP address from request headers."""
    # Check for forwarded headers
    forwarded_headers = [
        "X-Forwarded-For",
        "X-Real-IP",
        "X-Client-IP",
        "CF-Connecting-IP"  # Cloudflare
    ]
    
    for header in forwarded_headers:
        if header in headers:
            ip = headers[header].split(",")[0].strip()
            if ip and ip != "unknown":
                return ip
    
    return None


def is_session_expired(last_activity: datetime, timeout_minutes: int = 30) -> bool:
    """Check if session has expired based on last activity."""
    if not last_activity:
        return True
    
    expiry_time = last_activity + timedelta(minutes=timeout_minutes)
    return datetime.utcnow() > expiry_time


def format_error_response(error: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format error response for API."""
    response = {
        "error": error,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if details:
        response["details"] = details
    
    return response


def format_success_response(data: Any, message: Optional[str] = None) -> Dict[str, Any]:
    """Format success response for API."""
    response = {
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if message:
        response["message"] = message
    
    return response


def calculate_bot_score(analysis_results: Dict[str, float]) -> float:
    """Calculate overall bot score from individual analysis results."""
    if not analysis_results:
        return 0.0
    
    # Weighted average of different detection methods
    weights = {
        "keystroke_pattern": 0.3,
        "mouse_behavior": 0.25,
        "scroll_pattern": 0.15,
        "focus_behavior": 0.1,
        "timing_pattern": 0.2
    }
    
    total_score = 0.0
    total_weight = 0.0
    
    for method, weight in weights.items():
        if method in analysis_results:
            total_score += analysis_results[method] * weight
            total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    return total_score / total_weight


def calculate_confidence_score(analysis_results: Dict[str, float], event_count: int) -> float:
    """Calculate confidence score based on analysis results and event count."""
    if event_count < 10:
        return 0.3  # Low confidence with few events
    
    if event_count < 50:
        return 0.6  # Medium confidence
    
    if event_count < 100:
        return 0.8  # High confidence
    
    return 0.95  # Very high confidence


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_json_dumps(obj: Any) -> str:
    """Safely serialize object to JSON string."""
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return str(obj) 