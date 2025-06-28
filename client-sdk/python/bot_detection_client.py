"""
Bot Detection Python Client SDK.

This module provides a Python client for interacting with the Bot Detection API,
including session management, event collection, and survey analysis.
"""

import requests
import json
import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BotDetectionClient:
    """Client for interacting with the Bot Detection API."""
    
    def __init__(self, api_base_url: str, api_key: Optional[str] = None):
        """
        Initialize the Bot Detection client.
        
        Args:
            api_base_url: Base URL of the Bot Detection API
            api_key: Optional API key for authentication
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key
        self.session_id = None
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
        
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'BotDetection-Python-Client/1.0.0'
        })
    
    def create_session(self, user_agent: Optional[str] = None, 
                      survey_id: Optional[str] = None,
                      respondent_id: Optional[str] = None) -> str:
        """
        Create a new session for bot detection.
        
        Args:
            user_agent: Optional user agent string
            survey_id: Optional survey ID for integration
            respondent_id: Optional respondent ID for integration
            
        Returns:
            str: Session ID
        """
        try:
            url = f"{self.api_base_url}/detection/sessions"
            
            data = {}
            if user_agent:
                data['user_agent'] = user_agent
            if survey_id:
                data['survey_id'] = survey_id
            if respondent_id:
                data['respondent_id'] = respondent_id
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            self.session_id = result['session_id']
            
            logger.info(f"Created session: {self.session_id}")
            return self.session_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    def send_events(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send behavior events to the API.
        
        Args:
            events: List of event dictionaries
            
        Returns:
            Dict[str, Any]: API response
        """
        if not self.session_id:
            raise ValueError("No active session. Call create_session() first.")
        
        try:
            url = f"{self.api_base_url}/detection/sessions/{self.session_id}/events"
            
            response = self.session.post(url, json=events)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Sent {result['events_processed']} events")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send events: {e}")
            raise
    
    def analyze_session(self) -> Dict[str, Any]:
        """
        Analyze the current session for bot detection.
        
        Returns:
            Dict[str, Any]: Analysis results
        """
        if not self.session_id:
            raise ValueError("No active session. Call create_session() first.")
        
        try:
            url = f"{self.api_base_url}/detection/sessions/{self.session_id}/analyze"
            
            response = self.session.post(url)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Analysis completed: is_bot={result['is_bot']}, confidence={result['confidence_score']}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to analyze session: {e}")
            raise
    
    def get_session_status(self) -> Dict[str, Any]:
        """
        Get the current session status.
        
        Returns:
            Dict[str, Any]: Session status information
        """
        if not self.session_id:
            raise ValueError("No active session. Call create_session() first.")
        
        try:
            url = f"{self.api_base_url}/detection/sessions/{self.session_id}/status"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get session status: {e}")
            raise
    
    def create_keystroke_event(self, key: str, element_id: Optional[str] = None,
                              element_type: Optional[str] = None,
                              page_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a keystroke event.
        
        Args:
            key: The key that was pressed
            element_id: ID of the element that received the keystroke
            element_type: Type of the element
            page_url: Current page URL
            
        Returns:
            Dict[str, Any]: Event data
        """
        return {
            'event_type': 'keystroke',
            'timestamp': datetime.utcnow().isoformat(),
            'key': key,
            'element_id': element_id,
            'element_type': element_type,
            'page_url': page_url,
            'event_data': {
                'key': key,
                'element_id': element_id,
                'element_type': element_type
            }
        }
    
    def create_mouse_click_event(self, x: int, y: int, button: int = 1,
                                element_id: Optional[str] = None,
                                element_type: Optional[str] = None,
                                page_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a mouse click event.
        
        Args:
            x: X coordinate of the click
            y: Y coordinate of the click
            button: Mouse button (1=left, 2=middle, 3=right)
            element_id: ID of the clicked element
            element_type: Type of the clicked element
            page_url: Current page URL
            
        Returns:
            Dict[str, Any]: Event data
        """
        return {
            'event_type': 'mouse_click',
            'timestamp': datetime.utcnow().isoformat(),
            'x': x,
            'y': y,
            'button': button,
            'element_id': element_id,
            'element_type': element_type,
            'page_url': page_url,
            'event_data': {
                'x': x,
                'y': y,
                'button': button,
                'element_id': element_id,
                'element_type': element_type
            }
        }
    
    def create_mouse_move_event(self, x: int, y: int, 
                               page_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a mouse move event.
        
        Args:
            x: X coordinate of the mouse position
            y: Y coordinate of the mouse position
            page_url: Current page URL
            
        Returns:
            Dict[str, Any]: Event data
        """
        return {
            'event_type': 'mouse_move',
            'timestamp': datetime.utcnow().isoformat(),
            'x': x,
            'y': y,
            'page_url': page_url,
            'event_data': {
                'x': x,
                'y': y
            }
        }
    
    def create_scroll_event(self, scroll_x: int, scroll_y: int,
                           page_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a scroll event.
        
        Args:
            scroll_x: Horizontal scroll position
            scroll_y: Vertical scroll position
            page_url: Current page URL
            
        Returns:
            Dict[str, Any]: Event data
        """
        return {
            'event_type': 'scroll',
            'timestamp': datetime.utcnow().isoformat(),
            'scroll_x': scroll_x,
            'scroll_y': scroll_y,
            'page_url': page_url,
            'event_data': {
                'scroll_x': scroll_x,
                'scroll_y': scroll_y
            }
        }
    
    def create_focus_event(self, element_id: str, element_type: Optional[str] = None,
                          page_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a focus event.
        
        Args:
            element_id: ID of the focused element
            element_type: Type of the focused element
            page_url: Current page URL
            
        Returns:
            Dict[str, Any]: Event data
        """
        return {
            'event_type': 'focus',
            'timestamp': datetime.utcnow().isoformat(),
            'element_id': element_id,
            'element_type': element_type,
            'page_url': page_url,
            'event_data': {
                'element_id': element_id,
                'element_type': element_type
            }
        }
    
    def create_blur_event(self, element_id: str, element_type: Optional[str] = None,
                         page_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a blur event.
        
        Args:
            element_id: ID of the blurred element
            element_type: Type of the blurred element
            page_url: Current page URL
            
        Returns:
            Dict[str, Any]: Event data
        """
        return {
            'event_type': 'blur',
            'timestamp': datetime.utcnow().isoformat(),
            'element_id': element_id,
            'element_type': element_type,
            'page_url': page_url,
            'event_data': {
                'element_id': element_id,
                'element_type': element_type
            }
        }
    
    def create_page_load_event(self, page_url: str, page_title: Optional[str] = None,
                              load_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Create a page load event.
        
        Args:
            page_url: URL of the loaded page
            page_title: Title of the page
            load_time: Page load time in milliseconds
            
        Returns:
            Dict[str, Any]: Event data
        """
        return {
            'event_type': 'page_load',
            'timestamp': datetime.utcnow().isoformat(),
            'page_url': page_url,
            'page_title': page_title,
            'load_time': load_time,
            'event_data': {
                'page_url': page_url,
                'page_title': page_title,
                'load_time': load_time
            }
        }
    
    def analyze_qualtrics_survey(self, survey_id: str, response_id: str) -> Dict[str, Any]:
        """
        Analyze a Qualtrics survey response.
        
        Args:
            survey_id: Qualtrics survey ID
            response_id: Qualtrics response ID
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            url = f"{self.api_base_url}/integrations/qualtrics/analyze"
            
            data = {
                'survey_id': survey_id,
                'response_id': response_id
            }
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to analyze Qualtrics survey: {e}")
            raise
    
    def analyze_decipher_survey(self, survey_id: str, response_id: str) -> Dict[str, Any]:
        """
        Analyze a Decipher survey response.
        
        Args:
            survey_id: Decipher survey ID
            response_id: Decipher response ID
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            url = f"{self.api_base_url}/integrations/decipher/analyze"
            
            data = {
                'survey_id': survey_id,
                'response_id': response_id
            }
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to analyze Decipher survey: {e}")
            raise 