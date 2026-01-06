"""
Detection Controller.

This controller handles bot detection API endpoints including session creation,
event ingestion, and detection result retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any
import logging

from app.database import get_db
from app.models import Session, BehaviorData, DetectionResult
from app.services import BotDetectionEngine
from app.utils.logger import setup_logger
from app.utils.helpers import validate_event_data, sanitize_user_agent, is_valid_ip_address

logger = setup_logger(__name__)

class DetectionController:
    """Controller for bot detection endpoints."""
    
    def __init__(self):
        """Initialize the detection controller."""
        self.router = APIRouter(prefix="/detection", tags=["detection"])
        self.detection_engine = BotDetectionEngine()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes for detection endpoints."""
        
        @self.router.post("/sessions")
        async def create_session(
            request: Request,
            survey_id: str = None,
            platform: str = None,  # Kept for backward compatibility
            platform_id: str = None,  # New hierarchical field
            respondent_id: str = None,
            db: AsyncSession = Depends(get_db)
        ):
            """Create a new session for bot detection."""
            try:
                # Extract client information
                user_agent = request.headers.get("user-agent", "")
                ip_address = request.client.host if request.client else None
                referrer = request.headers.get("referer", "")
                
                # Sanitize inputs
                user_agent = sanitize_user_agent(user_agent)
                if ip_address and not is_valid_ip_address(ip_address):
                    ip_address = None
                
                # Use platform_id if provided, otherwise fall back to platform for backward compatibility
                final_platform_id = platform_id if platform_id else platform
                
                # Create session
                session = Session(
                    user_agent=user_agent,
                    ip_address=ip_address,
                    referrer=referrer,
                    survey_id=survey_id,
                    platform=platform,  # Keep for backward compatibility
                    platform_id=final_platform_id,  # New hierarchical field
                    respondent_id=respondent_id
                )
                
                db.add(session)
                await db.commit()
                await db.refresh(session)
                
                logger.info(f"Created session: {session.id}")
                
                return {
                    "session_id": session.id,
                    "created_at": session.created_at.isoformat(),
                    "status": "active"
                }
                
            except Exception as e:
                logger.error(f"Error creating session: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                await db.rollback()
                
                # In development/debug mode, return detailed error
                from app.config import settings
                if settings.DEBUG:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to create session: {type(e).__name__}: {str(e)}"
                    )
                else:
                    raise HTTPException(status_code=500, detail="Failed to create session")
        
        @self.router.post("/sessions/{session_id}/events")
        async def ingest_events(
            session_id: str,
            events: List[Dict[str, Any]],
            db: AsyncSession = Depends(get_db)
        ):
            """Ingest behavior events for a session."""
            try:
                # Validate session exists
                session_query = select(Session).where(Session.id == session_id)
                session_result = await db.execute(session_query)
                session = session_result.scalar_one_or_none()
                
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                if not session.is_active:
                    raise HTTPException(status_code=400, detail="Session is not active")
                
                # Validate and process events
                valid_events = []
                for event_data in events:
                    if validate_event_data(event_data):
                        # Convert timestamp
                        from datetime import datetime
                        if isinstance(event_data['timestamp'], str):
                            timestamp = datetime.fromisoformat(event_data['timestamp'].replace('Z', '+00:00'))
                        else:
                            timestamp = datetime.fromtimestamp(event_data['timestamp'])
                        
                        # Create behavior data record
                        behavior_data = BehaviorData(
                            session_id=session_id,
                            event_type=event_data['event_type'],
                            timestamp=timestamp,
                            event_data=event_data,
                            element_id=event_data.get('element_id'),
                            element_type=event_data.get('element_type'),
                            element_class=event_data.get('element_class'),
                            page_url=event_data.get('page_url'),
                            page_title=event_data.get('page_title'),
                            screen_width=event_data.get('screen_width'),
                            screen_height=event_data.get('screen_height'),
                            viewport_width=event_data.get('viewport_width'),
                            viewport_height=event_data.get('viewport_height'),
                            load_time=event_data.get('load_time'),
                            response_time=event_data.get('response_time')
                        )
                        
                        valid_events.append(behavior_data)
                    else:
                        logger.warning(f"Invalid event data: {event_data}")
                
                # Save valid events
                if valid_events:
                    db.add_all(valid_events)
                    await db.commit()
                    
                    # Update session last activity
                    session.last_activity = valid_events[-1].timestamp
                    await db.commit()
                
                logger.info(f"Ingested {len(valid_events)} events for session {session_id}")
                
                return {
                    "session_id": session_id,
                    "events_processed": len(valid_events),
                    "total_events": len(events),
                    "status": "success"
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error ingesting events: {e}")
                await db.rollback()
                raise HTTPException(status_code=500, detail="Failed to ingest events")
        
        @self.router.get("/sessions/{session_id}/ready-for-analysis")
        async def check_session_ready(
            session_id: str,
            db: AsyncSession = Depends(get_db)
        ):
            """Check if a session is ready for bot detection analysis."""
            try:
                # Validate session exists
                session_query = select(Session).where(Session.id == session_id)
                session_result = await db.execute(session_query)
                session = session_result.scalar_one_or_none()
                
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                # Get behavior data count
                behavior_count_query = select(func.count(BehaviorData.id)).where(BehaviorData.session_id == session_id)
                behavior_count_result = await db.execute(behavior_count_query)
                behavior_count = behavior_count_result.scalar()
                
                # Get latest detection result
                detection_query = (
                    select(DetectionResult)
                    .where(DetectionResult.session_id == session_id)
                    .order_by(DetectionResult.created_at.desc())
                    .limit(1)
                )
                detection_result = await db.execute(detection_query)
                latest_detection = detection_result.scalar_one_or_none()
                
                return {
                    "session_id": session_id,
                    "is_ready": behavior_count > 0,
                    "event_count": behavior_count,
                    "has_previous_analysis": latest_detection is not None,
                    "last_analysis": latest_detection.analyzed_at.isoformat() if latest_detection else None,
                    "message": "Session is ready for analysis" if behavior_count > 0 else "No behavior data found. Add events first."
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error checking session readiness: {e}")
                raise HTTPException(status_code=500, detail="Failed to check session readiness")
        
        @self.router.post("/sessions/{session_id}/analyze")
        async def analyze_session(
            session_id: str,
            db: AsyncSession = Depends(get_db)
        ):
            """Analyze a session for bot detection."""
            try:
                # Validate session exists
                session_query = select(Session).where(Session.id == session_id)
                session_result = await db.execute(session_query)
                session = session_result.scalar_one_or_none()
                
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                # Get behavior data for the session
                behavior_query = select(BehaviorData).where(BehaviorData.session_id == session_id)
                behavior_result = await db.execute(behavior_query)
                behavior_data = behavior_result.scalars().all()
                
                logger.info(f"Found {len(behavior_data)} behavior events for session {session_id}")
                
                if not behavior_data:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Session {session_id} has no behavior data to analyze. Please add events first using POST /api/v1/detection/sessions/{session_id}/events"
                    )
                
                # Perform bot detection analysis
                detection_result = await self.detection_engine.analyze_session(behavior_data)
                
                # Set the session_id explicitly
                detection_result.session_id = session_id
                
                # Save detection result
                db.add(detection_result)
                await db.commit()
                await db.refresh(detection_result)
                
                logger.info(f"Analysis completed for session {session_id}: is_bot={detection_result.is_bot}")
                
                return {
                    "session_id": session_id,
                    "is_bot": detection_result.is_bot,
                    "confidence_score": detection_result.confidence_score,
                    "risk_level": detection_result.risk_level,
                    "processing_time_ms": detection_result.processing_time_ms,
                    "event_count": detection_result.event_count,
                    "analysis_summary": detection_result.analysis_summary,
                    "detection_methods": detection_result.detection_methods,
                    "method_scores": detection_result.method_scores,
                    "flagged_patterns": detection_result.flagged_patterns,
                    "analyzed_at": detection_result.analyzed_at.isoformat()
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error analyzing session: {e}")
                logger.error(f"Error type: {type(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                await db.rollback()
                raise HTTPException(status_code=500, detail="Failed to analyze session")
        
        @self.router.post("/sessions/{session_id}/composite-analyze")
        async def composite_analyze_session(
            session_id: str,
            db: AsyncSession = Depends(get_db)
        ):
            """Analyze a session with composite scoring (behavioral + text quality)."""
            try:
                # Validate session exists
                session_query = select(Session).where(Session.id == session_id)
                session_result = await db.execute(session_query)
                session = session_result.scalar_one_or_none()
                
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                # Calculate composite score
                composite_result = await self.detection_engine.calculate_composite_score(session_id, db)
                
                logger.info(f"Composite analysis completed for session {session_id}: score={composite_result['composite_score']:.3f}")
                
                return composite_result
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error in composite analysis: {e}")
                raise HTTPException(status_code=500, detail="Failed to perform composite analysis")
        
        @self.router.get("/sessions/{session_id}/status")
        async def get_session_status(
            session_id: str,
            db: AsyncSession = Depends(get_db)
        ):
            """Get session status and latest detection result."""
            try:
                # Get session with latest detection result
                session_query = select(Session).where(Session.id == session_id)
                session_result = await db.execute(session_query)
                session = session_result.scalar_one_or_none()
                
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                # Get latest detection result
                detection_query = (
                    select(DetectionResult)
                    .where(DetectionResult.session_id == session_id)
                    .order_by(DetectionResult.created_at.desc())
                    .limit(1)
                )
                detection_result = await db.execute(detection_query)
                latest_detection = detection_result.scalar_one_or_none()
                
                # Get event count
                event_count_query = select(BehaviorData).where(BehaviorData.session_id == session_id)
                event_result = await db.execute(event_count_query)
                event_count = len(event_result.scalars().all())
                
                response = {
                    "session_id": session_id,
                    "status": "active" if session.is_active else "inactive",
                    "created_at": session.created_at.isoformat(),
                    "last_activity": session.last_activity.isoformat(),
                    "event_count": event_count,
                    "platform": session.platform,
                    "survey_id": session.survey_id,
                    "respondent_id": session.respondent_id
                }
                
                if latest_detection:
                    response["latest_detection"] = {
                        "is_bot": latest_detection.is_bot,
                        "confidence_score": latest_detection.confidence_score,
                        "risk_level": latest_detection.risk_level,
                        "analyzed_at": latest_detection.analyzed_at.isoformat(),
                        "analysis_summary": latest_detection.analysis_summary
                    }
                
                return response
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting session status: {e}")
                raise HTTPException(status_code=500, detail="Failed to get session status")
    
    def get_router(self) -> APIRouter:
        """Get the router for this controller."""
        return self.router 