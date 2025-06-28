"""
Helper utility functions.

This module contains common utility functions used throughout the application
for data validation, ID generation, and other helper operations.
"""

import uuid
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re

def generate_session_id() -> str:
    """
    Generate a unique session ID.
    
    Returns:
        str: Unique session identifier
    """
    return str(uuid.uuid4())

def validate_event_data(event_data: Dict[str, Any]) -> bool:
    """
    Validate event data structure and required fields.
    
    Args:
        event_data: Event data dictionary to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = ['event_type', 'timestamp']
    
    # Check required fields
    for field in required_fields:
        if field not in event_data:
            return False
    
    # Validate event type
    valid_event_types = [
        'keystroke', 'mouse_move', 'mouse_click', 'mouse_drag',
        'scroll', 'focus', 'blur', 'page_load', 'form_submit'
    ]
    
    if event_data['event_type'] not in valid_event_types:
        return False
    
    # Validate timestamp
    try:
        if isinstance(event_data['timestamp'], str):
            datetime.fromisoformat(event_data['timestamp'].replace('Z', '+00:00'))
        elif isinstance(event_data['timestamp'], (int, float)):
            datetime.fromtimestamp(event_data['timestamp'])
    except (ValueError, TypeError):
        return False
    
    return True

def calculate_confidence_score(method_scores: Dict[str, float]) -> float:
    """
    Calculate overall confidence score from individual method scores.
    
    Args:
        method_scores: Dictionary of method names to scores
        
    Returns:
        float: Weighted average confidence score (0.0 to 1.0)
    """
    if not method_scores:
        return 0.0
    
    # Weight different methods based on reliability
    weights = {
        'keystroke_analysis': 0.3,
        'mouse_analysis': 0.25,
        'timing_analysis': 0.2,
        'device_analysis': 0.15,
        'network_analysis': 0.1
    }
    
    total_score = 0.0
    total_weight = 0.0
    
    for method, score in method_scores.items():
        weight = weights.get(method, 0.1)  # Default weight for unknown methods
        total_score += score * weight
        total_weight += weight
    
    return total_score / total_weight if total_weight > 0 else 0.0

def determine_risk_level(confidence_score: float, is_bot: bool) -> str:
    """
    Determine risk level based on confidence score and bot detection.
    
    Args:
        confidence_score: Confidence score (0.0 to 1.0)
        is_bot: Whether the session was classified as a bot
        
    Returns:
        str: Risk level ('low', 'medium', 'high', 'critical')
    """
    if is_bot:
        if confidence_score >= 0.9:
            return 'critical'
        elif confidence_score >= 0.7:
            return 'high'
        elif confidence_score >= 0.5:
            return 'medium'
        else:
            return 'low'
    else:
        if confidence_score >= 0.9:
            return 'low'
        elif confidence_score >= 0.7:
            return 'low'
        elif confidence_score >= 0.5:
            return 'medium'
        else:
            return 'high'  # Low confidence in human classification

def sanitize_user_agent(user_agent: str) -> str:
    """
    Sanitize user agent string for safe storage.
    
    Args:
        user_agent: Raw user agent string
        
    Returns:
        str: Sanitized user agent string
    """
    if not user_agent:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', user_agent)
    
    # Limit length
    return sanitized[:500]

def is_valid_ip_address(ip_address: str) -> bool:
    """
    Validate IP address format.
    
    Args:
        ip_address: IP address string to validate
        
    Returns:
        bool: True if valid IP address format
    """
    if not ip_address:
        return False
    
    # IPv4 pattern
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(ipv4_pattern, ip_address):
        parts = ip_address.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    
    # IPv6 pattern (simplified)
    ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
    return bool(re.match(ipv6_pattern, ip_address))

def format_processing_time(start_time: float) -> float:
    """
    Calculate and format processing time in milliseconds.
    
    Args:
        start_time: Start time from time.time()
        
    Returns:
        float: Processing time in milliseconds
    """
    return (time.time() - start_time) * 1000 