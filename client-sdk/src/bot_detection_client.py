"""
Bot Detection Python Client SDK.

This module provides a Python client for the Bot Detection API,
allowing easy integration with Python applications.
"""

import requests
import json
import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime


class BotDetectionClient:
    """Python client for the Bot Detection API."""
    
    def __init__(self, api_base_url: str = "http://localhost:8000/api/v1", api_key: Optional[str] = None):
        """
        Initialize the Bot Detection client.
        
        Args:
            api_base_url: Base URL for the API
            api_key: Optional API key for authentication
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key
        self.session_id = None
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'BotDetection-Python-Client/1.0.0'
        })
        
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}'
            })
    
    def create_session(self, user_agent: Optional[str] = None, referrer: Optional[str] = None) -> str:
        """
        Create a new session for bot detection tracking.
        
        Args:
            user_agent: Optional user agent string
            referrer: Optional referrer URL
            
        Returns:
            Session ID
        """
        url = f"{self.api_base_url}/detection/sessions"
        payload = {}
        
        if user_agent:
            payload['user_agent'] = user_agent
        if referrer:
            payload['referrer'] = referrer
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        self.session_id = data['session_id']
        
        return self.session_id
    
    def send_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send behavior events for analysis.
        
        Args:
            events: List of behavior events
            
        Returns:
            Analysis results
        """
        if not self.session_id:
            raise ValueError("No active session. Call create_session() first.")
        
        url = f"{self.api_base_url}/detection/sessions/{self.session_id}/data"
        payload = {'events': events}
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def get_session_status(self) -> Dict[str, Any]:
        """
        Get current session status and latest results.
        
        Returns:
            Session status information
        """
        if not self.session_id:
            raise ValueError("No active session. Call create_session() first.")
        
        url = f"{self.api_base_url}/detection/sessions/{self.session_id}/status"
        response = self.session.get(url)
        response.raise_for_status()
        
        return response.json()
    
    def get_session_events(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get behavior events for the current session.
        
        Args:
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            List of behavior events
        """
        if not self.session_id:
            raise ValueError("No active session. Call create_session() first.")
        
        url = f"{self.api_base_url}/detection/sessions/{self.session_id}/events"
        params = {'limit': limit, 'offset': offset}
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get('data', [])
    
    def get_session_results(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get detection results for the current session.
        
        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of detection results
        """
        if not self.session_id:
            raise ValueError("No active session. Call create_session() first.")
        
        url = f"{self.api_base_url}/detection/sessions/{self.session_id}/results"
        params = {'limit': limit, 'offset': offset}
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get('data', [])
    
    def create_keystroke_event(self, key_code: int, key_char: str, 
                              element_id: Optional[str] = None, 
                              element_type: Optional[str] = None,
                              page_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a keystroke event.
        
        Args:
            key_code: Key code
            key_char: Key character
            element_id: Element ID
            element_type: Element type
            page_url: Page URL
            
        Returns:
            Event data
        """
        return {
            'event_type': 'keystroke',
            'event_data': {
                'key_code': key_code,
                'key_char': key_char,
                'timestamp': time.time()
            },
            'element_id': element_id,
            'element_type': element_type,
            'page_url': page_url
        }
    
    def create_mouse_event(self, event_type: str, x: int, y: int,
                          button: Optional[int] = None,
                          element_id: Optional[str] = None,
                          element_type: Optional[str] = None,
                          page_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a mouse event.
        
        Args:
            event_type: Event type (click, move, etc.)
            x: X coordinate
            y: Y coordinate
            button: Mouse button
            element_id: Element ID
            element_type: Element type
            page_url: Page URL
            
        Returns:
            Event data
        """
        return {
            'event_type': f'mouse_{event_type}',
            'event_data': {
                'x': x,
                'y': y,
                'button': button,
                'timestamp': time.time()
            },
            'element_id': element_id,
            'element_type': element_type,
            'page_url': page_url
        }
    
    def create_scroll_event(self, scroll_x: int, scroll_y: int,
                           page_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a scroll event.
        
        Args:
            scroll_x: Horizontal scroll position
            scroll_y: Vertical scroll position
            page_url: Page URL
            
        Returns:
            Event data
        """
        return {
            'event_type': 'scroll',
            'event_data': {
                'scroll_x': scroll_x,
                'scroll_y': scroll_y,
                'timestamp': time.time()
            },
            'page_url': page_url
        }
    
    def create_focus_event(self, event_type: str, element_id: Optional[str] = None,
                          element_type: Optional[str] = None,
                          page_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a focus event.
        
        Args:
            event_type: Event type (focus, blur)
            element_id: Element ID
            element_type: Element type
            page_url: Page URL
            
        Returns:
            Event data
        """
        return {
            'event_type': f'focus_{event_type}',
            'event_data': {
                'element_id': element_id,
                'element_type': element_type,
                'timestamp': time.time()
            },
            'element_id': element_id,
            'element_type': element_type,
            'page_url': page_url
        }
    
    def analyze_survey_responses(self, survey_id: str, platform: str,
                                start_date: Optional[str] = None,
                                end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze survey responses for bot detection.
        
        Args:
            survey_id: Survey ID
            platform: Platform name (qualtrics, decipher)
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            Analysis results
        """
        url = f"{self.api_base_url}/integrations/{platform}/analyze"
        payload = {
            'survey_id': survey_id,
            'platform': platform
        }
        
        if start_date:
            payload['start_date'] = start_date
        if end_date:
            payload['end_date'] = end_date
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def get_dashboard_metrics(self, start_date: Optional[str] = None,
                             end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get dashboard metrics.
        
        Args:
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            Dashboard metrics
        """
        url = f"{self.api_base_url}/dashboard/metrics/summary"
        params = {}
        
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_timeseries_data(self, interval: str = "hour", days: int = 7) -> List[Dict[str, Any]]:
        """
        Get time series data for charts.
        
        Args:
            interval: Time interval (hour, day, week)
            days: Number of days to look back
            
        Returns:
            Time series data
        """
        url = f"{self.api_base_url}/dashboard/metrics/timeseries"
        params = {
            'interval': interval,
            'days': days
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get('data', [])
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent sessions.
        
        Args:
            limit: Number of sessions to return
            
        Returns:
            List of recent sessions
        """
        url = f"{self.api_base_url}/dashboard/sessions/recent"
        params = {'limit': limit}
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get('data', [])
    
    def get_integration_status(self) -> List[Dict[str, Any]]:
        """
        Get integration status.
        
        Returns:
            List of integration statuses
        """
        url = f"{self.api_base_url}/integrations/status"
        response = self.session.get(url)
        response.raise_for_status()
        
        data = response.json()
        return data.get('data', [])
    
    def close(self):
        """Close the client session."""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience functions for quick usage
def create_session(api_base_url: str = "http://localhost:8000/api/v1", 
                  api_key: Optional[str] = None,
                  user_agent: Optional[str] = None,
                  referrer: Optional[str] = None) -> BotDetectionClient:
    """
    Create a new Bot Detection client and session.
    
    Args:
        api_base_url: Base URL for the API
        api_key: Optional API key for authentication
        user_agent: Optional user agent string
        referrer: Optional referrer URL
        
    Returns:
        BotDetectionClient instance with active session
    """
    client = BotDetectionClient(api_base_url, api_key)
    client.create_session(user_agent, referrer)
    return client


def analyze_events(events: List[Dict[str, Any]], 
                  api_base_url: str = "http://localhost:8000/api/v1",
                  api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze events without creating a persistent session.
    
    Args:
        events: List of behavior events
        api_base_url: Base URL for the API
        api_key: Optional API key for authentication
        
    Returns:
        Analysis results
    """
    with BotDetectionClient(api_base_url, api_key) as client:
        client.create_session()
        return client.send_events(events) 