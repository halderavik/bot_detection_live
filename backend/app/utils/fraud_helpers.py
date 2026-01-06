"""
Fraud detection helper utilities.

This module contains utility functions for fraud detection including
device fingerprinting, text similarity, IP geolocation, and fraud scoring.
"""

import hashlib
import difflib
import ipaddress
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from app.models import Session, BehaviorData


def generate_device_fingerprint(session: Session, behavior_data: list[BehaviorData]) -> str:
    """
    Generate a device fingerprint hash from session and behavior data.
    
    Args:
        session: Session object with device metadata
        behavior_data: List of behavior data events
        
    Returns:
        str: SHA256 hash of device fingerprint
    """
    # Collect device characteristics
    fingerprint_components = []
    
    # User agent
    fingerprint_components.append(session.user_agent or "")
    
    # Screen dimensions (use first available event)
    screen_width = None
    screen_height = None
    viewport_width = None
    viewport_height = None
    
    for event in behavior_data:
        if screen_width is None and event.screen_width:
            screen_width = event.screen_width
        if screen_height is None and event.screen_height:
            screen_height = event.screen_height
        if viewport_width is None and event.viewport_width:
            viewport_width = event.viewport_width
        if viewport_height is None and event.viewport_height:
            viewport_height = event.viewport_height
        
        if all([screen_width, screen_height, viewport_width, viewport_height]):
            break
    
    fingerprint_components.append(str(screen_width) if screen_width else "")
    fingerprint_components.append(str(screen_height) if screen_height else "")
    fingerprint_components.append(str(viewport_width) if viewport_width else "")
    fingerprint_components.append(str(viewport_height) if viewport_height else "")
    
    # Platform ID
    fingerprint_components.append(session.platform_id or "")
    
    # Combine all components
    fingerprint_string = "|".join(fingerprint_components)
    
    # Generate SHA256 hash
    fingerprint_hash = hashlib.sha256(fingerprint_string.encode('utf-8')).hexdigest()
    
    return fingerprint_hash


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two text strings.
    
    Uses sequence matching (difflib) to compute similarity ratio.
    
    Args:
        text1: First text string
        text2: Second text string
        
    Returns:
        float: Similarity score (0.0 to 1.0, where 1.0 is identical)
    """
    if not text1 or not text2:
        return 0.0
    
    # Normalize text (lowercase, strip whitespace)
    text1_normalized = text1.lower().strip()
    text2_normalized = text2.lower().strip()
    
    if text1_normalized == text2_normalized:
        return 1.0
    
    # Use SequenceMatcher for similarity
    similarity = difflib.SequenceMatcher(None, text1_normalized, text2_normalized).ratio()
    
    return similarity


def get_ip_country_code(ip_address: str) -> Optional[str]:
    """
    Get country code from IP address using basic IP range lookup.
    
    This is a basic implementation. For production, consider using
    a service like MaxMind GeoIP2 or IPinfo.
    
    Args:
        ip_address: IP address string
        
    Returns:
        Optional[str]: Two-letter country code or None
    """
    if not ip_address:
        return None
    
    try:
        # Parse IP address
        ip = ipaddress.ip_address(ip_address)
        
        # Check if it's a private/local IP
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return None
        
        # Basic country code mapping for common IP ranges
        # This is a simplified implementation
        # In production, use a proper GeoIP database
        
        # For now, return None (can be enhanced with IP range database)
        return None
        
    except (ValueError, AttributeError):
        return None


def extract_geolocation_from_ip(ip_address: str) -> Dict[str, Optional[str]]:
    """
    Extract geolocation information from IP address.
    
    Args:
        ip_address: IP address string
        
    Returns:
        Dict with country_code and city (both may be None)
    """
    country_code = get_ip_country_code(ip_address)
    
    return {
        "country_code": country_code,
        "city": None  # City lookup would require a more sophisticated service
    }


def calculate_fraud_risk_level(fraud_score: float) -> str:
    """
    Map fraud score to risk level.
    
    Args:
        fraud_score: Fraud score (0.0 to 1.0)
        
    Returns:
        str: Risk level (LOW, MEDIUM, HIGH, CRITICAL)
    """
    if fraud_score >= 0.9:
        return "CRITICAL"
    elif fraud_score >= 0.7:
        return "HIGH"
    elif fraud_score >= 0.4:
        return "MEDIUM"
    else:
        return "LOW"


def calculate_weighted_fraud_score(
    ip_score: float,
    fingerprint_score: float,
    duplicate_score: float,
    geolocation_score: float,
    velocity_score: float
) -> float:
    """
    Calculate overall fraud score from individual method scores using weights.
    
    Args:
        ip_score: IP analysis score (0.0-1.0)
        fingerprint_score: Device fingerprint score (0.0-1.0)
        duplicate_score: Duplicate response score (0.0-1.0)
        geolocation_score: Geolocation score (0.0-1.0)
        velocity_score: Velocity score (0.0-1.0)
        
    Returns:
        float: Weighted fraud score (0.0-1.0)
    """
    weights = {
        "ip": 0.25,
        "fingerprint": 0.25,
        "duplicate": 0.20,
        "geolocation": 0.15,
        "velocity": 0.15
    }
    
    weighted_score = (
        ip_score * weights["ip"] +
        fingerprint_score * weights["fingerprint"] +
        duplicate_score * weights["duplicate"] +
        geolocation_score * weights["geolocation"] +
        velocity_score * weights["velocity"]
    )
    
    return min(max(weighted_score, 0.0), 1.0)


def calculate_ip_risk_score(usage_count: int, sessions_today: int) -> float:
    """
    Calculate IP risk score based on usage frequency.
    
    Args:
        usage_count: Total number of sessions using this IP
        sessions_today: Number of sessions from this IP today
        
    Returns:
        float: Risk score (0.0-1.0)
    """
    # Risk increases with more usage
    if usage_count >= 10 or sessions_today >= 5:
        return 0.8
    elif usage_count >= 5 or sessions_today >= 3:
        return 0.6
    elif usage_count >= 3:
        return 0.4
    elif usage_count >= 2:
        return 0.2
    else:
        return 0.0


def calculate_fingerprint_risk_score(usage_count: int) -> float:
    """
    Calculate device fingerprint risk score based on reuse count.
    
    Args:
        usage_count: Number of sessions with matching fingerprint
        
    Returns:
        float: Risk score (0.0-1.0)
    """
    if usage_count >= 5:
        return 0.9
    elif usage_count >= 3:
        return 0.7
    elif usage_count >= 2:
        return 0.5
    else:
        return 0.0


def calculate_duplicate_response_risk_score(similarity: float) -> float:
    """
    Calculate risk score based on response similarity.
    
    Args:
        similarity: Text similarity score (0.0-1.0)
        
    Returns:
        float: Risk score (0.0-1.0)
    """
    if similarity >= 0.95:
        return 1.0
    elif similarity >= 0.85:
        return 0.8
    elif similarity >= 0.70:
        return 0.6
    else:
        return 0.0


def calculate_velocity_risk_score(responses_per_hour: float) -> float:
    """
    Calculate velocity risk score based on submission rate.
    
    Args:
        responses_per_hour: Number of responses per hour
        
    Returns:
        float: Risk score (0.0-1.0)
    """
    if responses_per_hour >= 20:
        return 1.0
    elif responses_per_hour >= 10:
        return 0.8
    elif responses_per_hour >= 5:
        return 0.6
    elif responses_per_hour >= 3:
        return 0.4
    else:
        return 0.0
