"""
Decipher Integration Service.

This service handles integration with Decipher survey platform,
including webhook handling, response validation, and data synchronization.
"""

import aiohttp
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.utils.logger import setup_logger
from app.config import settings

logger = setup_logger(__name__)

class DecipherIntegration:
    """Service for integrating with Decipher survey platform."""
    
    def __init__(self):
        """Initialize Decipher integration with API configuration."""
        self.api_key = settings.DECIPHER_API_KEY
        self.base_url = "https://v2.decipherinc.com/api/v1"
        self.webhook_url = f"{settings.BASE_URL}/api/v1/webhooks/decipher"
        
        if not self.api_key:
            logger.warning("Decipher API key not configured")
    
    async def validate_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Validate webhook signature from Decipher.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature header
            
        Returns:
            bool: True if signature is valid
        """
        # Decipher uses HMAC-SHA256 for webhook signatures
        try:
            import hmac
            import hashlib
            
            # This is a placeholder - actual implementation depends on Decipher setup
            expected_signature = hmac.new(
                self.api_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error validating webhook signature: {e}")
            return False
    
    async def process_survey_response(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process survey response webhook from Decipher.
        
        Args:
            webhook_data: Webhook payload from Decipher
            
        Returns:
            Dict[str, Any]: Processed response data
        """
        try:
            # Extract relevant data from webhook
            response_id = webhook_data.get('responseId')
            survey_id = webhook_data.get('surveyId')
            respondent_id = webhook_data.get('respondentId')
            
            # Get detailed response data
            response_data = await self._get_response_details(survey_id, response_id)
            
            # Extract bot detection related fields
            bot_detection_data = self._extract_bot_detection_data(response_data)
            
            processed_data = {
                'platform': 'decipher',
                'survey_id': survey_id,
                'response_id': response_id,
                'respondent_id': respondent_id,
                'response_data': response_data,
                'bot_detection_data': bot_detection_data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Processed Decipher response: {response_id}")
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing Decipher webhook: {e}")
            raise
    
    async def _get_response_details(self, survey_id: str, response_id: str) -> Dict[str, Any]:
        """
        Get detailed response data from Decipher API.
        
        Args:
            survey_id: Decipher survey ID
            response_id: Response ID to retrieve
            
        Returns:
            Dict[str, Any]: Detailed response data
        """
        if not self.api_key:
            raise ValueError("Decipher API key not configured")
        
        url = f"{self.base_url}/surveys/{survey_id}/responses/{response_id}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', {})
                else:
                    error_text = await response.text()
                    logger.error(f"Decipher API error: {response.status} - {error_text}")
                    raise Exception(f"Decipher API error: {response.status}")
    
    def _extract_bot_detection_data(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract bot detection related data from survey response.
        
        Args:
            response_data: Raw response data from Decipher
            
        Returns:
            Dict[str, Any]: Extracted bot detection data
        """
        bot_data = {}
        
        # Extract system variables (Decipher's equivalent of embedded data)
        system_vars = response_data.get('systemVariables', {})
        
        # Look for bot detection fields
        bot_fields = [
            'bot_detection_session_id',
            'bot_detection_score',
            'bot_detection_confidence',
            'bot_detection_risk_level',
            'user_agent',
            'ip_address',
            'session_duration'
        ]
        
        for field in bot_fields:
            if field in system_vars:
                bot_data[field] = system_vars[field]
        
        # Extract from question responses
        questions = response_data.get('questions', {})
        
        # Look for bot detection questions (custom question IDs)
        bot_question_ids = [
            'bot_session_id',
            'bot_detection_score',
            'user_agent_info',
            'ip_address_info'
        ]
        
        for qid in bot_question_ids:
            if qid in questions:
                bot_data[qid] = questions[qid].get('value')
        
        return bot_data
    
    async def update_response_with_detection(self, survey_id: str, response_id: str, 
                                           detection_result: Dict[str, Any]) -> bool:
        """
        Update survey response with bot detection results.
        
        Args:
            survey_id: Decipher survey ID
            response_id: Response ID to update
            detection_result: Bot detection results
            
        Returns:
            bool: True if update was successful
        """
        if not self.api_key:
            logger.warning("Cannot update response - API key not configured")
            return False
        
        try:
            # Prepare system variables update
            system_vars = {
                'bot_detection_result': json.dumps(detection_result),
                'bot_detection_timestamp': datetime.utcnow().isoformat(),
                'bot_detection_confidence': detection_result.get('confidence_score', 0),
                'bot_detection_risk_level': detection_result.get('risk_level', 'unknown')
            }
            
            url = f"{self.base_url}/surveys/{survey_id}/responses/{response_id}"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'systemVariables': system_vars
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.put(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Updated Decipher response {response_id} with detection results")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to update Decipher response: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error updating Decipher response: {e}")
            return False
    
    async def get_survey_info(self, survey_id: str) -> Optional[Dict[str, Any]]:
        """
        Get survey information from Decipher.
        
        Args:
            survey_id: Decipher survey ID
            
        Returns:
            Optional[Dict[str, Any]]: Survey information
        """
        if not self.api_key:
            return None
        
        try:
            url = f"{self.base_url}/surveys/{survey_id}"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {})
                    else:
                        logger.warning(f"Could not fetch survey info: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching survey info: {e}")
            return None
    
    async def create_webhook(self, survey_id: str, webhook_url: str) -> bool:
        """
        Create a webhook for survey responses.
        
        Args:
            survey_id: Decipher survey ID
            webhook_url: URL to receive webhooks
            
        Returns:
            bool: True if webhook was created successfully
        """
        if not self.api_key:
            logger.warning("Cannot create webhook - API key not configured")
            return False
        
        try:
            url = f"{self.base_url}/surveys/{survey_id}/webhooks"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'url': webhook_url,
                'events': ['response.completed'],
                'active': True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 201:
                        logger.info(f"Created webhook for survey {survey_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create webhook: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error creating webhook: {e}")
            return False 