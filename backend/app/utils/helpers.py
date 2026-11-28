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

# How far each check alone can move the bot probability. Evidence from separate checks
# adds up (a noisy-OR): one strong check is a lead, two agreeing checks reach the bot
# threshold. A weighted average could never get there: a perfect keyboard score and a
# perfect mouse score averaged to 0.61, below 0.7.
METHOD_RELIABILITY = {
    'keystroke_analysis': 0.5,
    'mouse_analysis': 0.45,
    'timing_analysis': 0.35,
    'device_analysis': 0.4,
    # Network analysis is not implemented yet; it adds nothing.
    'network_analysis': 0.0,
}


def calculate_confidence_score(method_scores: Dict[str, float]) -> float:
    """
    Combine the per-check bot scores into one bot probability.

    Each check's score (0-1) times its reliability is its chance of meaning "bot";
    the result is the chance that at least one of them does: 1 - prod(1 - r * s).

    Args:
        method_scores: Dictionary of method names to scores

    Returns:
        float: Bot probability (0.0 to 1.0)
    """
    if not method_scores:
        return 0.0
    remaining = 1.0
    for method, score in method_scores.items():
        reliability = METHOD_RELIABILITY.get(method, 0.2)
        remaining *= 1.0 - reliability * min(max(float(score or 0.0), 0.0), 1.0)
    return 1.0 - remaining

def determine_risk_level(confidence_score: float, is_bot: bool) -> str:
    """
    Determine risk level from the bot probability.

    ``confidence_score`` is the probability that the session is a bot (0.0 = human,
    1.0 = bot), so a low score is low risk whatever the verdict.

    Args:
        confidence_score: Bot probability (0.0 to 1.0)
        is_bot: Whether the session was classified as a bot

    Returns:
        str: Risk level ('low', 'medium', 'high', 'critical')
    """
    if confidence_score >= 0.9:
        return 'critical'
    if confidence_score >= 0.7 or is_bot:
        return 'high'
    if confidence_score >= 0.5:
        return 'medium'
    return 'low'

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


def client_ip(request) -> Optional[str]:
    """
    The respondent's IP address.

    Behind Cloud Run's front end, ``request.client.host`` is the proxy's internal
    address, the same for everyone. The real address is the right-most public entry
    of X-Forwarded-For (entries to its left can be supplied by the client).
    """
    import ipaddress

    forwarded = request.headers.get("x-forwarded-for", "")
    for candidate in reversed([part.strip() for part in forwarded.split(",") if part.strip()]):
        try:
            address = ipaddress.ip_address(candidate)
        except ValueError:
            continue
        if address.is_global:
            return str(address)
    return request.client.host if request.client else None
