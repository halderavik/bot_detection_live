"""
Qualtrics integration service.

This module provides integration with Qualtrics survey platform
for bot detection in survey responses.
"""

import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from utils.logger import get_logger
from config.config import settings

logger = get_logger(__name__)


class QualtricsIntegration:
    """Qualtrics platform integration for bot detection."""
    
    def __init__(self):
        """Initialize Qualtrics integration."""
        self.api_key = settings.QUALTRICS_API_KEY
        self.base_url = "https://iad1.qualtrics.com/API/v3"
        self.headers = {
            "X-API-TOKEN": self.api_key,
            "Content-Type": "application/json"
        }
    
    def get_survey_responses(self, survey_id: str, start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve survey responses from Qualtrics.
        
        Args:
            survey_id: Qualtrics survey ID
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            
        Returns:
            List of survey responses
        """
        try:
            url = f"{self.base_url}/surveys/{survey_id}/responses"
            params = {}
            
            if start_date:
                params["startDate"] = start_date
            if end_date:
                params["endDate"] = end_date
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get("result", {}).get("elements", [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch Qualtrics responses: {e}")
            return []
    
    def get_response_details(self, survey_id: str, response_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific response.
        
        Args:
            survey_id: Qualtrics survey ID
            response_id: Response ID
            
        Returns:
            Response details or None if failed
        """
        try:
            url = f"{self.base_url}/surveys/{survey_id}/responses/{response_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json().get("result", {})
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch response details: {e}")
            return None
    
    def extract_behavior_data(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract behavior data from Qualtrics response.
        
        Args:
            response_data: Raw response data from Qualtrics
            
        Returns:
            List of behavior events
        """
        events = []
        
        try:
            # Extract embedded data (custom fields)
            embedded_data = response_data.get("embeddedData", {})
            
            # Extract timing data
            timing_data = embedded_data.get("timing", {})
            if timing_data:
                events.extend(self._parse_timing_data(timing_data))
            
            # Extract mouse/click data
            click_data = embedded_data.get("clicks", {})
            if click_data:
                events.extend(self._parse_click_data(click_data))
            
            # Extract keystroke data
            keystroke_data = embedded_data.get("keystrokes", {})
            if keystroke_data:
                events.extend(self._parse_keystroke_data(keystroke_data))
            
            # Extract scroll data
            scroll_data = embedded_data.get("scrolls", {})
            if scroll_data:
                events.extend(self._parse_scroll_data(scroll_data))
            
        except Exception as e:
            logger.error(f"Failed to extract behavior data: {e}")
        
        return events
    
    def _parse_timing_data(self, timing_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse timing data from Qualtrics response."""
        events = []
        
        try:
            # Parse question timing
            for question_id, timing_info in timing_data.items():
                if isinstance(timing_info, dict) and "start" in timing_info and "end" in timing_info:
                    events.append({
                        "event_type": "question_timing",
                        "event_data": {
                            "question_id": question_id,
                            "start_time": timing_info.get("start"),
                            "end_time": timing_info.get("end"),
                            "duration": timing_info.get("end", 0) - timing_info.get("start", 0)
                        },
                        "timestamp": timing_info.get("start", 0)
                    })
        except Exception as e:
            logger.error(f"Failed to parse timing data: {e}")
        
        return events
    
    def _parse_click_data(self, click_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse click data from Qualtrics response."""
        events = []
        
        try:
            for click_info in click_data:
                if isinstance(click_info, dict):
                    events.append({
                        "event_type": "mouse_click",
                        "event_data": {
                            "x": click_info.get("x"),
                            "y": click_info.get("y"),
                            "element_id": click_info.get("elementId"),
                            "timestamp": click_info.get("timestamp")
                        },
                        "timestamp": click_info.get("timestamp", 0)
                    })
        except Exception as e:
            logger.error(f"Failed to parse click data: {e}")
        
        return events
    
    def _parse_keystroke_data(self, keystroke_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse keystroke data from Qualtrics response."""
        events = []
        
        try:
            for keystroke_info in keystroke_data:
                if isinstance(keystroke_info, dict):
                    events.append({
                        "event_type": "keystroke",
                        "event_data": {
                            "key_code": keystroke_info.get("keyCode"),
                            "key_char": keystroke_info.get("keyChar"),
                            "timestamp": keystroke_info.get("timestamp")
                        },
                        "timestamp": keystroke_info.get("timestamp", 0)
                    })
        except Exception as e:
            logger.error(f"Failed to parse keystroke data: {e}")
        
        return events
    
    def _parse_scroll_data(self, scroll_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse scroll data from Qualtrics response."""
        events = []
        
        try:
            for scroll_info in scroll_data:
                if isinstance(scroll_info, dict):
                    events.append({
                        "event_type": "scroll",
                        "event_data": {
                            "scroll_x": scroll_info.get("scrollX", 0),
                            "scroll_y": scroll_info.get("scrollY", 0),
                            "timestamp": scroll_info.get("timestamp")
                        },
                        "timestamp": scroll_info.get("timestamp", 0)
                    })
        except Exception as e:
            logger.error(f"Failed to parse scroll data: {e}")
        
        return events
    
    def flag_response_as_bot(self, survey_id: str, response_id: str, 
                           bot_score: float, analysis_details: Dict[str, Any]) -> bool:
        """
        Flag a response as potentially from a bot in Qualtrics.
        
        Args:
            survey_id: Qualtrics survey ID
            response_id: Response ID
            bot_score: Bot detection score
            analysis_details: Detailed analysis results
            
        Returns:
            True if successfully flagged, False otherwise
        """
        try:
            # Update embedded data with bot detection results
            embedded_data = {
                "bot_detection_score": bot_score,
                "bot_detection_timestamp": datetime.utcnow().isoformat(),
                "bot_detection_details": json.dumps(analysis_details),
                "is_potential_bot": bot_score >= 0.7
            }
            
            url = f"{self.base_url}/surveys/{survey_id}/responses/{response_id}"
            payload = {
                "embeddedData": embedded_data
            }
            
            response = requests.put(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            logger.info(f"Successfully flagged response {response_id} as potential bot")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to flag response as bot: {e}")
            return False
    
    def get_survey_metadata(self, survey_id: str) -> Optional[Dict[str, Any]]:
        """
        Get survey metadata from Qualtrics.
        
        Args:
            survey_id: Qualtrics survey ID
            
        Returns:
            Survey metadata or None if failed
        """
        try:
            url = f"{self.base_url}/surveys/{survey_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json().get("result", {})
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch survey metadata: {e}")
            return None
    
    def is_configured(self) -> bool:
        """Check if Qualtrics integration is properly configured."""
        return bool(self.api_key and self.api_key != "") 