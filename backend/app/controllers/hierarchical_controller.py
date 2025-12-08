"""
Hierarchical controller for survey-platform-respondent-session structure.

This controller provides hierarchical endpoints for navigating and aggregating
data at different levels: Survey → Platform → Respondent → Session.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.database import get_db
from app.services.aggregation_service import AggregationService
from app.models import Session, DetectionResult, BehaviorData
from app.utils.logger import setup_logger
from sqlalchemy import select, func

logger = setup_logger(__name__)

class HierarchicalController:
    """Controller for hierarchical API endpoints."""
    
    def __init__(self):
        """Initialize the hierarchical controller."""
        self.router = APIRouter(prefix="/surveys", tags=["Hierarchical API"])
        self.aggregation_service = AggregationService()
        self._setup_routes()
    
    def get_router(self) -> APIRouter:
        """Get the router for this controller."""
        return self.router
    
    def _setup_routes(self):
        """Setup API routes for hierarchical endpoints."""
        
        # Survey Level Endpoints
        @self.router.get("")
        async def list_surveys(
            limit: int = Query(100, ge=1, le=1000, description="Maximum number of surveys to return"),
            offset: int = Query(0, ge=0, description="Offset for pagination"),
            db: AsyncSession = Depends(get_db)
        ):
            """List all surveys with aggregated statistics."""
            try:
                surveys = await self.aggregation_service.list_surveys(db, limit=limit, offset=offset)
                return {
                    "surveys": surveys,
                    "total": len(surveys),
                    "limit": limit,
                    "offset": offset
                }
            except Exception as e:
                logger.error(f"Error listing surveys: {e}")
                raise HTTPException(status_code=500, detail="Failed to list surveys")
        
        @self.router.get("/{survey_id}")
        async def get_survey_details(
            survey_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get survey details with aggregated metrics."""
            try:
                # Parse dates if provided
                date_from_dt = None
                date_to_dt = None
                
                if date_from:
                    try:
                        date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_from format")
                
                if date_to:
                    try:
                        date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_to format")
                
                aggregation = await self.aggregation_service.get_survey_aggregation(
                    survey_id, db, date_from=date_from_dt, date_to=date_to_dt
                )
                
                return aggregation
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting survey details: {e}")
                raise HTTPException(status_code=500, detail="Failed to get survey details")
        
        @self.router.get("/{survey_id}/summary")
        async def get_survey_summary(
            survey_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get survey summary with key metrics."""
            try:
                # Parse dates if provided
                date_from_dt = None
                date_to_dt = None
                
                if date_from:
                    try:
                        date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_from format")
                
                if date_to:
                    try:
                        date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_to format")
                
                aggregation = await self.aggregation_service.get_survey_aggregation(
                    survey_id, db, date_from=date_from_dt, date_to=date_to_dt
                )
                
                # Return summary format
                return {
                    "survey_id": survey_id,
                    "summary": {
                        "total_respondents": aggregation["total_respondents"],
                        "total_sessions": aggregation["total_sessions"],
                        "total_platforms": aggregation["total_platforms"],
                        "bot_rate": aggregation["bot_detection"]["bot_rate"],
                        "avg_confidence": aggregation["bot_detection"]["avg_confidence"],
                        "avg_quality_score": aggregation["text_quality"]["avg_quality_score"],
                        "flagged_percentage": aggregation["text_quality"]["flagged_percentage"]
                    },
                    "platform_distribution": aggregation["platform_distribution"],
                    "risk_distribution": aggregation["risk_distribution"]
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting survey summary: {e}")
                raise HTTPException(status_code=500, detail="Failed to get survey summary")
        
        # Platform Level Endpoints
        @self.router.get("/{survey_id}/platforms")
        async def list_platforms(
            survey_id: str,
            db: AsyncSession = Depends(get_db)
        ):
            """List all platforms for a survey."""
            try:
                platforms = await self.aggregation_service.list_platforms(survey_id, db)
                return {
                    "survey_id": survey_id,
                    "platforms": platforms,
                    "total": len(platforms)
                }
            except Exception as e:
                logger.error(f"Error listing platforms: {e}")
                raise HTTPException(status_code=500, detail="Failed to list platforms")
        
        @self.router.get("/{survey_id}/platforms/{platform_id}")
        async def get_platform_details(
            survey_id: str,
            platform_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get platform details with aggregated metrics."""
            try:
                # Parse dates if provided
                date_from_dt = None
                date_to_dt = None
                
                if date_from:
                    try:
                        date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_from format")
                
                if date_to:
                    try:
                        date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_to format")
                
                aggregation = await self.aggregation_service.get_platform_aggregation(
                    survey_id, platform_id, db, date_from=date_from_dt, date_to=date_to_dt
                )
                
                return aggregation
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting platform details: {e}")
                raise HTTPException(status_code=500, detail="Failed to get platform details")
        
        @self.router.get("/{survey_id}/platforms/{platform_id}/summary")
        async def get_platform_summary(
            survey_id: str,
            platform_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get platform summary with key metrics."""
            try:
                # Parse dates if provided
                date_from_dt = None
                date_to_dt = None
                
                if date_from:
                    try:
                        date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_from format")
                
                if date_to:
                    try:
                        date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_to format")
                
                aggregation = await self.aggregation_service.get_platform_aggregation(
                    survey_id, platform_id, db, date_from=date_from_dt, date_to=date_to_dt
                )
                
                # Return summary format
                return {
                    "survey_id": survey_id,
                    "platform_id": platform_id,
                    "summary": {
                        "total_respondents": aggregation["total_respondents"],
                        "total_sessions": aggregation["total_sessions"],
                        "bot_rate": aggregation["bot_detection"]["bot_rate"],
                        "avg_confidence": aggregation["bot_detection"]["avg_confidence"],
                        "avg_quality_score": aggregation["text_quality"]["avg_quality_score"],
                        "flagged_percentage": aggregation["text_quality"]["flagged_percentage"]
                    }
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting platform summary: {e}")
                raise HTTPException(status_code=500, detail="Failed to get platform summary")
        
        # Respondent Level Endpoints
        @self.router.get("/{survey_id}/platforms/{platform_id}/respondents")
        async def list_respondents(
            survey_id: str,
            platform_id: str,
            limit: int = Query(100, ge=1, le=1000, description="Maximum number of respondents to return"),
            offset: int = Query(0, ge=0, description="Offset for pagination"),
            db: AsyncSession = Depends(get_db)
        ):
            """List all respondents for a platform."""
            try:
                respondents = await self.aggregation_service.list_respondents(
                    survey_id, platform_id, db, limit=limit, offset=offset
                )
                return {
                    "survey_id": survey_id,
                    "platform_id": platform_id,
                    "respondents": respondents,
                    "total": len(respondents),
                    "limit": limit,
                    "offset": offset
                }
            except Exception as e:
                logger.error(f"Error listing respondents: {e}")
                raise HTTPException(status_code=500, detail="Failed to list respondents")
        
        @self.router.get("/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}")
        async def get_respondent_details(
            survey_id: str,
            platform_id: str,
            respondent_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get respondent details with aggregated metrics across all sessions."""
            try:
                # Parse dates if provided
                date_from_dt = None
                date_to_dt = None
                
                if date_from:
                    try:
                        date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_from format")
                
                if date_to:
                    try:
                        date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_to format")
                
                aggregation = await self.aggregation_service.get_respondent_aggregation(
                    survey_id, platform_id, respondent_id, db,
                    date_from=date_from_dt, date_to=date_to_dt
                )
                
                return aggregation
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting respondent details: {e}")
                raise HTTPException(status_code=500, detail="Failed to get respondent details")
        
        @self.router.get("/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/summary")
        async def get_respondent_summary(
            survey_id: str,
            platform_id: str,
            respondent_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get respondent summary with key metrics aggregated across all sessions."""
            try:
                # Parse dates if provided
                date_from_dt = None
                date_to_dt = None
                
                if date_from:
                    try:
                        date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_from format")
                
                if date_to:
                    try:
                        date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_to format")
                
                aggregation = await self.aggregation_service.get_respondent_aggregation(
                    survey_id, platform_id, respondent_id, db,
                    date_from=date_from_dt, date_to=date_to_dt
                )
                
                # Return summary format
                return {
                    "survey_id": survey_id,
                    "platform_id": platform_id,
                    "respondent_id": respondent_id,
                    "summary": {
                        "total_sessions": aggregation["total_sessions"],
                        "bot_rate": aggregation["bot_detection"]["bot_rate"],
                        "avg_confidence": aggregation["bot_detection"]["avg_confidence"],
                        "overall_risk": aggregation["bot_detection"]["overall_risk"],
                        "avg_quality_score": aggregation["text_quality"]["avg_quality_score"],
                        "flagged_percentage": aggregation["text_quality"]["flagged_percentage"]
                    },
                    "session_timeline": aggregation["session_timeline"]
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting respondent summary: {e}")
                raise HTTPException(status_code=500, detail="Failed to get respondent summary")
        
        @self.router.get("/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions")
        async def list_respondent_sessions(
            survey_id: str,
            platform_id: str,
            respondent_id: str,
            limit: int = Query(100, ge=1, le=1000, description="Maximum number of sessions to return"),
            offset: int = Query(0, ge=0, description="Offset for pagination"),
            db: AsyncSession = Depends(get_db)
        ):
            """List all sessions for a respondent."""
            try:
                aggregation = await self.aggregation_service.get_respondent_aggregation(
                    survey_id, platform_id, respondent_id, db
                )
                
                # Apply pagination
                sessions = aggregation.get("sessions", [])
                total = len(sessions)
                paginated_sessions = sessions[offset:offset + limit]
                
                return {
                    "survey_id": survey_id,
                    "platform_id": platform_id,
                    "respondent_id": respondent_id,
                    "sessions": paginated_sessions,
                    "total": total,
                    "limit": limit,
                    "offset": offset
                }
                
            except Exception as e:
                logger.error(f"Error listing respondent sessions: {e}")
                raise HTTPException(status_code=500, detail="Failed to list respondent sessions")
        
        # Session Level Endpoint (hierarchical path)
        @self.router.get("/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}")
        async def get_session_by_hierarchy(
            survey_id: str,
            platform_id: str,
            respondent_id: str,
            session_id: str,
            db: AsyncSession = Depends(get_db)
        ):
            """Get session details via hierarchical path."""
            try:
                # Verify session belongs to this hierarchy
                session_query = select(Session).where(
                    Session.id == session_id,
                    Session.survey_id == survey_id,
                    Session.platform_id == platform_id,
                    Session.respondent_id == respondent_id
                )
                
                result = await db.execute(session_query)
                session = result.scalar_one_or_none()
                
                if not session:
                    raise HTTPException(
                        status_code=404,
                        detail="Session not found in the specified hierarchy"
                    )
                
                # Get session details (reuse existing endpoint logic)
                # For now, return basic session info - can be enhanced later
                # Get event count
                event_count_query = select(func.count(BehaviorData.id)).where(
                    BehaviorData.session_id == session_id
                )
                event_result = await db.execute(event_count_query)
                event_count = event_result.scalar() or 0
                
                # Get latest detection
                detection_query = (
                    select(DetectionResult)
                    .where(DetectionResult.session_id == session_id)
                    .order_by(DetectionResult.created_at.desc())
                    .limit(1)
                )
                detection_result = await db.execute(detection_query)
                latest_detection = detection_result.scalar_one_or_none()
                
                return {
                    "survey_id": survey_id,
                    "platform_id": platform_id,
                    "respondent_id": respondent_id,
                    "session_id": session_id,
                    "session": {
                        "id": session.id,
                        "created_at": session.created_at.isoformat() if session.created_at else None,
                        "is_active": session.is_active,
                        "is_completed": session.is_completed,
                        "user_agent": session.user_agent,
                        "ip_address": session.ip_address,
                        "event_count": event_count
                    },
                    "latest_detection": {
                        "is_bot": latest_detection.is_bot if latest_detection else None,
                        "confidence_score": float(latest_detection.confidence_score) if latest_detection and latest_detection.confidence_score else None,
                        "risk_level": latest_detection.risk_level if latest_detection else None,
                        "created_at": latest_detection.created_at.isoformat() if latest_detection and latest_detection.created_at else None
                    } if latest_detection else None
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting session by hierarchy: {e}")
                raise HTTPException(status_code=500, detail="Failed to get session details")

