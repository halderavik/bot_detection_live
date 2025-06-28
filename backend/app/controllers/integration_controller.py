"""
Integration Controller.

This controller handles integration endpoints for survey platforms
including webhook processing and platform-specific integrations.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, Optional
import logging

from app.database import get_db
from app.models import Session, DetectionResult
from app.services import QualtricsIntegration, DecipherIntegration
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class IntegrationController:
    """Controller for integration endpoints."""
    
    def __init__(self):
        """Initialize the integration controller."""
        self.router = APIRouter(prefix="/integrations", tags=["integrations"])
        self.qualtrics = QualtricsIntegration()
        self.decipher = DecipherIntegration()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes for integration endpoints."""
        
        @self.router.post("/webhooks/qualtrics")
        async def qualtrics_webhook(
            request: Request,
            x_qualtrics_signature: Optional[str] = Header(None),
            db: AsyncSession = Depends(get_db)
        ):
            """Handle Qualtrics webhook for survey responses."""
            try:
                # Get raw payload
                payload = await request.body()
                payload_str = payload.decode('utf-8')
                
                # Validate webhook signature
                if x_qualtrics_signature:
                    if not await self.qualtrics.validate_webhook_signature(payload_str, x_qualtrics_signature):
                        logger.warning("Invalid Qualtrics webhook signature")
                        raise HTTPException(status_code=401, detail="Invalid signature")
                
                # Parse JSON payload
                import json
                webhook_data = json.loads(payload_str)
                
                # Process the webhook
                processed_data = await self.qualtrics.process_survey_response(webhook_data)
                
                # Extract bot detection session ID if available
                bot_data = processed_data.get('bot_detection_data', {})
                session_id = bot_data.get('bot_detection_session_id')
                
                if session_id:
                    # Update session with survey information
                    session_query = select(Session).where(Session.id == session_id)
                    session_result = await db.execute(session_query)
                    session = session_result.scalar_one_or_none()
                    
                    if session:
                        session.survey_id = processed_data.get('survey_id')
                        session.respondent_id = processed_data.get('respondent_id')
                        session.platform = 'qualtrics'
                        session.is_completed = True
                        await db.commit()
                        
                        # Get latest detection result
                        detection_query = (
                            select(DetectionResult)
                            .where(DetectionResult.session_id == session_id)
                            .order_by(DetectionResult.created_at.desc())
                            .limit(1)
                        )
                        detection_result = await db.execute(detection_query)
                        latest_detection = detection_result.scalar_one_or_none()
                        
                        if latest_detection:
                            # Update Qualtrics response with detection results
                            detection_data = {
                                'is_bot': latest_detection.is_bot,
                                'confidence_score': latest_detection.confidence_score,
                                'risk_level': latest_detection.risk_level,
                                'analysis_summary': latest_detection.analysis_summary,
                                'method_scores': latest_detection.method_scores
                            }
                            
                            await self.qualtrics.update_response_with_detection(
                                processed_data.get('survey_id'),
                                processed_data.get('response_id'),
                                detection_data
                            )
                
                logger.info(f"Processed Qualtrics webhook for response: {processed_data.get('response_id')}")
                
                return {"status": "success", "message": "Webhook processed successfully"}
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error processing Qualtrics webhook: {e}")
                raise HTTPException(status_code=500, detail="Failed to process webhook")
        
        @self.router.post("/webhooks/decipher")
        async def decipher_webhook(
            request: Request,
            x_decipher_signature: Optional[str] = Header(None),
            db: AsyncSession = Depends(get_db)
        ):
            """Handle Decipher webhook for survey responses."""
            try:
                # Get raw payload
                payload = await request.body()
                payload_str = payload.decode('utf-8')
                
                # Validate webhook signature
                if x_decipher_signature:
                    if not await self.decipher.validate_webhook_signature(payload_str, x_decipher_signature):
                        logger.warning("Invalid Decipher webhook signature")
                        raise HTTPException(status_code=401, detail="Invalid signature")
                
                # Parse JSON payload
                import json
                webhook_data = json.loads(payload_str)
                
                # Process the webhook
                processed_data = await self.decipher.process_survey_response(webhook_data)
                
                # Extract bot detection session ID if available
                bot_data = processed_data.get('bot_detection_data', {})
                session_id = bot_data.get('bot_detection_session_id')
                
                if session_id:
                    # Update session with survey information
                    session_query = select(Session).where(Session.id == session_id)
                    session_result = await db.execute(session_query)
                    session = session_result.scalar_one_or_none()
                    
                    if session:
                        session.survey_id = processed_data.get('survey_id')
                        session.respondent_id = processed_data.get('respondent_id')
                        session.platform = 'decipher'
                        session.is_completed = True
                        await db.commit()
                        
                        # Get latest detection result
                        detection_query = (
                            select(DetectionResult)
                            .where(DetectionResult.session_id == session_id)
                            .order_by(DetectionResult.created_at.desc())
                            .limit(1)
                        )
                        detection_result = await db.execute(detection_query)
                        latest_detection = detection_result.scalar_one_or_none()
                        
                        if latest_detection:
                            # Update Decipher response with detection results
                            detection_data = {
                                'is_bot': latest_detection.is_bot,
                                'confidence_score': latest_detection.confidence_score,
                                'risk_level': latest_detection.risk_level,
                                'analysis_summary': latest_detection.analysis_summary,
                                'method_scores': latest_detection.method_scores
                            }
                            
                            await self.decipher.update_response_with_detection(
                                processed_data.get('survey_id'),
                                processed_data.get('response_id'),
                                detection_data
                            )
                
                logger.info(f"Processed Decipher webhook for response: {processed_data.get('response_id')}")
                
                return {"status": "success", "message": "Webhook processed successfully"}
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error processing Decipher webhook: {e}")
                raise HTTPException(status_code=500, detail="Failed to process webhook")
        
        @self.router.get("/qualtrics/surveys/{survey_id}")
        async def get_qualtrics_survey_info(survey_id: str):
            """Get information about a Qualtrics survey."""
            try:
                survey_info = await self.qualtrics.get_survey_info(survey_id)
                
                if not survey_info:
                    raise HTTPException(status_code=404, detail="Survey not found")
                
                return {
                    "platform": "qualtrics",
                    "survey_id": survey_id,
                    "survey_info": survey_info
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting Qualtrics survey info: {e}")
                raise HTTPException(status_code=500, detail="Failed to get survey information")
        
        @self.router.get("/decipher/surveys/{survey_id}")
        async def get_decipher_survey_info(survey_id: str):
            """Get information about a Decipher survey."""
            try:
                survey_info = await self.decipher.get_survey_info(survey_id)
                
                if not survey_info:
                    raise HTTPException(status_code=404, detail="Survey not found")
                
                return {
                    "platform": "decipher",
                    "survey_id": survey_id,
                    "survey_info": survey_info
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting Decipher survey info: {e}")
                raise HTTPException(status_code=500, detail="Failed to get survey information")
        
        @self.router.post("/qualtrics/surveys/{survey_id}/webhooks")
        async def create_qualtrics_webhook(
            survey_id: str,
            webhook_url: str
        ):
            """Create a webhook for a Qualtrics survey."""
            try:
                success = await self.qualtrics.create_webhook(survey_id, webhook_url)
                
                if not success:
                    raise HTTPException(status_code=400, detail="Failed to create webhook")
                
                return {
                    "status": "success",
                    "message": "Webhook created successfully",
                    "survey_id": survey_id,
                    "webhook_url": webhook_url
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error creating Qualtrics webhook: {e}")
                raise HTTPException(status_code=500, detail="Failed to create webhook")
        
        @self.router.post("/decipher/surveys/{survey_id}/webhooks")
        async def create_decipher_webhook(
            survey_id: str,
            webhook_url: str
        ):
            """Create a webhook for a Decipher survey."""
            try:
                success = await self.decipher.create_webhook(survey_id, webhook_url)
                
                if not success:
                    raise HTTPException(status_code=400, detail="Failed to create webhook")
                
                return {
                    "status": "success",
                    "message": "Webhook created successfully",
                    "survey_id": survey_id,
                    "webhook_url": webhook_url
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error creating Decipher webhook: {e}")
                raise HTTPException(status_code=500, detail="Failed to create webhook")
        
        @self.router.get("/status")
        async def get_integration_status():
            """Get status of all integrations."""
            try:
                status = {
                    "qualtrics": {
                        "enabled": bool(self.qualtrics.api_token),
                        "configured": bool(self.qualtrics.api_token)
                    },
                    "decipher": {
                        "enabled": bool(self.decipher.api_key),
                        "configured": bool(self.decipher.api_key)
                    }
                }
                
                return status
                
            except Exception as e:
                logger.error(f"Error getting integration status: {e}")
                raise HTTPException(status_code=500, detail="Failed to get integration status")
    
    def get_router(self) -> APIRouter:
        """Get the router for this controller."""
        return self.router 