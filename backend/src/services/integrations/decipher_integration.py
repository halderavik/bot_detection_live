"""
Decipher integration service.

This module provides integration with Decipher survey platform
for bot detection in survey responses.
"""

import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from utils.logger import get_logger
from config.config import settings

logger = get_logger(__name__)


class DecipherIntegration:
    """Decipher platform integration for bot detection."""
    
    def __init__(self):
        """Initialize Decipher integration."""
        self.api_key = settings.DECIPHER_API_KEY
        self.base_url = "https://v2.decipherinc.com/api"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_survey_responses(self, survey_id: str, start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve survey responses from Decipher.
        
        Args:
            survey_id: Decipher survey ID
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
            return data.get("responses", [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch Decipher responses: {e}")
            return []
    
    def get_response_details(self, survey_id: str, response_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific response.
        
        Args:
            survey_id: Decipher survey ID
            response_id: Response ID
            
        Returns:
            Response details or None if failed
        """
        try:
            url = f"{self.base_url}/surveys/{survey_id}/responses/{response_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch response details: {e}")
            return None
    
    def extract_behavior_data(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract behavior data from Decipher response.
        
        Args:
            response_data: Raw response data from Decipher
            
        Returns:
            List of behavior events
        """
        events = []
        
        try:
            # Extract custom variables (behavior data)
            custom_vars = response_data.get("customVariables", {})
            
            # Extract timing data
            timing_data = custom_vars.get("timing", {})
            if timing_data:
                events.extend(self._parse_timing_data(timing_data))
            
            # Extract mouse/click data
            click_data = custom_vars.get("clicks", {})
            if click_data:
                events.extend(self._parse_click_data(click_data))
            
            # Extract keystroke data
            keystroke_data = custom_vars.get("keystrokes", {})
            if keystroke_data:
                events.extend(self._parse_keystroke_data(keystroke_data))
            
            # Extract scroll data
            scroll_data = custom_vars.get("scrolls", {})
            if scroll_data:
                events.extend(self._parse_scroll_data(scroll_data))
            
            # Extract focus data
            focus_data = custom_vars.get("focus", {})
            if focus_data:
                events.extend(self._parse_focus_data(focus_data))
            
        except Exception as e:
            logger.error(f"Failed to extract behavior data: {e}")
        
        return events
    
    def _parse_timing_data(self, timing_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse timing data from Decipher response."""
        events = []
        
        try:
            # Parse question timing
            for question_id, timing_info in timing_data.items():
                if isinstance(timing_info, dict):
                    events.append({
                        "event_type": "question_timing",
                        "event_data": {
                            "question_id": question_id,
                            "start_time": timing_info.get("start"),
                            "end_time": timing_info.get("end"),
                            "duration": timing_info.get("duration")
                        },
                        "timestamp": timing_info.get("start", 0)
                    })
        except Exception as e:
            logger.error(f"Failed to parse timing data: {e}")
        
        return events
    
    def _parse_click_data(self, click_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse click data from Decipher response."""
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
                            "button": click_info.get("button", 1),
                            "timestamp": click_info.get("timestamp")
                        },
                        "timestamp": click_info.get("timestamp", 0)
                    })
        except Exception as e:
            logger.error(f"Failed to parse click data: {e}")
        
        return events
    
    def _parse_keystroke_data(self, keystroke_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse keystroke data from Decipher response."""
        events = []
        
        try:
            for keystroke_info in keystroke_data:
                if isinstance(keystroke_info, dict):
                    events.append({
                        "event_type": "keystroke",
                        "event_data": {
                            "key_code": keystroke_info.get("keyCode"),
                            "key_char": keystroke_info.get("keyChar"),
                            "key_type": keystroke_info.get("keyType", "keydown"),
                            "timestamp": keystroke_info.get("timestamp")
                        },
                        "timestamp": keystroke_info.get("timestamp", 0)
                    })
        except Exception as e:
            logger.error(f"Failed to parse keystroke data: {e}")
        
        return events
    
    def _parse_scroll_data(self, scroll_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse scroll data from Decipher response."""
        events = []
        
        try:
            for scroll_info in scroll_data:
                if isinstance(scroll_info, dict):
                    events.append({
                        "event_type": "scroll",
                        "event_data": {
                            "scroll_x": scroll_info.get("scrollX", 0),
                            "scroll_y": scroll_info.get("scrollY", 0),
                            "scroll_direction": scroll_info.get("direction", "vertical"),
                            "timestamp": scroll_info.get("timestamp")
                        },
                        "timestamp": scroll_info.get("timestamp", 0)
                    })
        except Exception as e:
            logger.error(f"Failed to parse scroll data: {e}")
        
        return events
    
    def _parse_focus_data(self, focus_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse focus/blur data from Decipher response."""
        events = []
        
        try:
            for focus_info in focus_data:
                if isinstance(focus_info, dict):
                    events.append({
                        "event_type": f"focus_{focus_info.get('type', 'change')}",
                        "event_data": {
                            "element_id": focus_info.get("elementId"),
                            "element_type": focus_info.get("elementType"),
                            "timestamp": focus_info.get("timestamp")
                        },
                        "timestamp": focus_info.get("timestamp", 0)
                    })
        except Exception as e:
            logger.error(f"Failed to parse focus data: {e}")
        
        return events
    
    def flag_response_as_bot(self, survey_id: str, response_id: str, 
                           bot_score: float, analysis_details: Dict[str, Any]) -> bool:
        """
        Flag a response as potentially from a bot in Decipher.
        
        Args:
            survey_id: Decipher survey ID
            response_id: Response ID
            bot_score: Bot detection score
            analysis_details: Detailed analysis results
            
        Returns:
            True if successfully flagged, False otherwise
        """
        try:
            # Update custom variables with bot detection results
            custom_vars = {
                "bot_detection_score": bot_score,
                "bot_detection_timestamp": datetime.utcnow().isoformat(),
                "bot_detection_details": json.dumps(analysis_details),
                "is_potential_bot": bot_score >= 0.7,
                "bot_risk_level": self._get_risk_level(bot_score)
            }
            
            url = f"{self.base_url}/surveys/{survey_id}/responses/{response_id}"
            payload = {
                "customVariables": custom_vars
            }
            
            response = requests.put(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            logger.info(f"Successfully flagged response {response_id} as potential bot")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to flag response as bot: {e}")
            return False
    
    def _get_risk_level(self, bot_score: float) -> str:
        """Get risk level based on bot score."""
        if bot_score >= 0.8:
            return "high"
        elif bot_score >= 0.6:
            return "medium"
        elif bot_score >= 0.4:
            return "low"
        else:
            return "very_low"
    
    def get_survey_metadata(self, survey_id: str) -> Optional[Dict[str, Any]]:
        """
        Get survey metadata from Decipher.
        
        Args:
            survey_id: Decipher survey ID
            
        Returns:
            Survey metadata or None if failed
        """
        try:
            url = f"{self.base_url}/surveys/{survey_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch survey metadata: {e}")
            return None
    
    def get_survey_questions(self, survey_id: str) -> List[Dict[str, Any]]:
        """
        Get survey questions from Decipher.
        
        Args:
            survey_id: Decipher survey ID
            
        Returns:
            List of survey questions
        """
        try:
            url = f"{self.base_url}/surveys/{survey_id}/questions"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get("questions", [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch survey questions: {e}")
            return []
    
    def export_responses(self, survey_id: str, format: str = "json", 
                        start_date: Optional[str] = None, 
                        end_date: Optional[str] = None) -> Optional[str]:
        """
        Export survey responses from Decipher.
        
        Args:
            survey_id: Decipher survey ID
            format: Export format (json, csv, xlsx)
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            Export file URL or None if failed
        """
        try:
            url = f"{self.base_url}/surveys/{survey_id}/export"
            params = {
                "format": format
            }
            
            if start_date:
                params["startDate"] = start_date
            if end_date:
                params["endDate"] = end_date
            
            response = requests.post(url, headers=self.headers, json=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get("exportUrl")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to export responses: {e}")
            return None
    
    def is_configured(self) -> bool:
        """Check if Decipher integration is properly configured."""
        return bool(self.api_key and self.api_key != "") 