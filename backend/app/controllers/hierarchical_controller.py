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
from app.models import Session, DetectionResult, BehaviorData, SurveyResponse, FraudIndicator
from app.utils.logger import setup_logger
from sqlalchemy import select, func, and_
from typing import List, Dict, Any
from datetime import datetime

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
        
        # Hierarchical Text Analysis Endpoints
        
        @self.router.get("/{survey_id}/text-analysis/summary")
        async def get_survey_text_analysis_summary(
            survey_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get text analysis summary for a survey."""
            try:
                # Build query conditions
                conditions = [
                    Session.survey_id == survey_id
                ]
                
                # Parse dates if provided
                date_from_dt = None
                date_to_dt = None
                
                if date_from:
                    try:
                        date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                        conditions.append(SurveyResponse.analyzed_at >= date_from_dt)
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_from format")
                
                if date_to:
                    try:
                        date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                        conditions.append(SurveyResponse.analyzed_at <= date_to_dt)
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_to format")
                
                # Query responses for this survey
                query = (
                    select(SurveyResponse)
                    .join(Session, SurveyResponse.session_id == Session.id)
                    .where(and_(*conditions))
                )
                
                result = await db.execute(query)
                responses = result.scalars().all()
                
                # Aggregate data
                aggregated = await self._aggregate_text_analysis(responses)
                
                logger.info(f"Survey text analysis summary generated for {survey_id}: {aggregated['total_responses']} responses")
                
                return {
                    "survey_id": survey_id,
                    **aggregated
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting survey text analysis summary: {e}")
                raise HTTPException(status_code=500, detail="Failed to get survey text analysis summary")
        
        @self.router.get("/{survey_id}/platforms/{platform_id}/text-analysis/summary")
        async def get_platform_text_analysis_summary(
            survey_id: str,
            platform_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get text analysis summary for a platform within a survey."""
            try:
                # Build query conditions
                conditions = [
                    Session.survey_id == survey_id,
                    Session.platform_id == platform_id
                ]
                
                # Parse dates if provided
                date_from_dt = None
                date_to_dt = None
                
                if date_from:
                    try:
                        date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                        conditions.append(SurveyResponse.analyzed_at >= date_from_dt)
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_from format")
                
                if date_to:
                    try:
                        date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                        conditions.append(SurveyResponse.analyzed_at <= date_to_dt)
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_to format")
                
                # Query responses for this platform
                query = (
                    select(SurveyResponse)
                    .join(Session, SurveyResponse.session_id == Session.id)
                    .where(and_(*conditions))
                )
                
                result = await db.execute(query)
                responses = result.scalars().all()
                
                # Aggregate data
                aggregated = await self._aggregate_text_analysis(responses)
                
                logger.info(f"Platform text analysis summary generated for {survey_id}/{platform_id}: {aggregated['total_responses']} responses")
                
                return {
                    "survey_id": survey_id,
                    "platform_id": platform_id,
                    **aggregated
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting platform text analysis summary: {e}")
                raise HTTPException(status_code=500, detail="Failed to get platform text analysis summary")
        
        @self.router.get("/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/text-analysis/summary")
        async def get_respondent_text_analysis_summary(
            survey_id: str,
            platform_id: str,
            respondent_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get text analysis summary for a respondent."""
            try:
                # Build query conditions
                conditions = [
                    Session.survey_id == survey_id,
                    Session.platform_id == platform_id,
                    Session.respondent_id == respondent_id
                ]
                
                # Parse dates if provided
                date_from_dt = None
                date_to_dt = None
                
                if date_from:
                    try:
                        date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                        conditions.append(SurveyResponse.analyzed_at >= date_from_dt)
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_from format")
                
                if date_to:
                    try:
                        date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                        conditions.append(SurveyResponse.analyzed_at <= date_to_dt)
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid date_to format")
                
                # Query responses for this respondent
                query = (
                    select(SurveyResponse)
                    .join(Session, SurveyResponse.session_id == Session.id)
                    .where(and_(*conditions))
                )
                
                result = await db.execute(query)
                responses = result.scalars().all()
                
                # Aggregate data
                aggregated = await self._aggregate_text_analysis(responses)
                
                # Get session count for this respondent
                session_query = select(func.count(Session.id)).where(
                    and_(
                        Session.survey_id == survey_id,
                        Session.platform_id == platform_id,
                        Session.respondent_id == respondent_id
                    )
                )
                session_result = await db.execute(session_query)
                session_count = session_result.scalar() or 0
                
                logger.info(f"Respondent text analysis summary generated for {survey_id}/{platform_id}/{respondent_id}: {aggregated['total_responses']} responses")
                
                return {
                    "survey_id": survey_id,
                    "platform_id": platform_id,
                    "respondent_id": respondent_id,
                    "session_count": session_count,
                    **aggregated
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting respondent text analysis summary: {e}")
                raise HTTPException(status_code=500, detail="Failed to get respondent text analysis summary")
        
        @self.router.get("/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/text-analysis")
        async def get_session_text_analysis_hierarchical(
            survey_id: str,
            platform_id: str,
            respondent_id: str,
            session_id: str,
            db: AsyncSession = Depends(get_db)
        ):
            """Get text analysis summary for a session via hierarchical path."""
            try:
                # Verify session belongs to this hierarchy
                session_query = select(Session).where(
                    and_(
                        Session.id == session_id,
                        Session.survey_id == survey_id,
                        Session.platform_id == platform_id,
                        Session.respondent_id == respondent_id
                    )
                )
                
                session_result = await db.execute(session_query)
                session = session_result.scalar_one_or_none()
                
                if not session:
                    raise HTTPException(
                        status_code=404,
                        detail="Session not found in the specified hierarchy"
                    )
                
                # Get all responses for the session
                responses_query = select(SurveyResponse).where(
                    SurveyResponse.session_id == session_id
                )
                responses_result = await db.execute(responses_query)
                responses = responses_result.scalars().all()
                
                # Aggregate data
                aggregated = await self._aggregate_text_analysis(responses)
                
                # Format response data
                response_data = []
                for response in responses:
                    response_data.append({
                        "response_id": response.id,
                        "question_id": response.question_id,
                        "quality_score": response.quality_score,
                        "is_flagged": response.is_flagged,
                        "flag_reasons": response.flag_reasons or {},
                        "analyzed_at": response.analyzed_at.isoformat() if response.analyzed_at else None,
                        "truncated_text": response.truncated_response_text
                    })
                
                logger.info(f"Session text analysis generated for {session_id}: {aggregated['total_responses']} responses")
                
                return {
                    "survey_id": survey_id,
                    "platform_id": platform_id,
                    "respondent_id": respondent_id,
                    "session_id": session_id,
                    **aggregated,
                    "responses": response_data
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting session text analysis: {e}")
                raise HTTPException(status_code=500, detail="Failed to get session text analysis")
        
        # Hierarchical Fraud Detection Endpoints
        
        @self.router.get("/{survey_id}/fraud/summary")
        async def get_survey_fraud_summary(
            survey_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get fraud detection summary for a survey."""
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
                
                # Aggregate fraud data using hierarchical parameters
                aggregated = await self._aggregate_fraud_data(
                    db, survey_id, date_from=date_from_dt, date_to=date_to_dt
                )
                
                logger.info(f"Survey fraud summary generated for {survey_id}")
                
                return {
                    "survey_id": survey_id,
                    **aggregated
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting survey fraud summary: {e}")
                raise HTTPException(status_code=500, detail="Failed to get survey fraud summary")
        
        @self.router.get("/{survey_id}/platforms/{platform_id}/fraud/summary")
        async def get_platform_fraud_summary(
            survey_id: str,
            platform_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get fraud detection summary for a platform within a survey."""
            try:
                # Build query conditions
                conditions = [
                    Session.survey_id == survey_id,
                    Session.platform_id == platform_id
                ]
                
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
                
                # Aggregate fraud data using hierarchical parameters
                aggregated = await self._aggregate_fraud_data(
                    db, survey_id, platform_id=platform_id, date_from=date_from_dt, date_to=date_to_dt
                )
                
                logger.info(f"Platform fraud summary generated for {survey_id}/{platform_id}")
                
                return {
                    "survey_id": survey_id,
                    "platform_id": platform_id,
                    **aggregated
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting platform fraud summary: {e}")
                raise HTTPException(status_code=500, detail="Failed to get platform fraud summary")
        
        @self.router.get("/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/fraud/summary")
        async def get_respondent_fraud_summary(
            survey_id: str,
            platform_id: str,
            respondent_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get fraud detection summary for a respondent."""
            try:
                # Build query conditions
                conditions = [
                    Session.survey_id == survey_id,
                    Session.platform_id == platform_id,
                    Session.respondent_id == respondent_id
                ]
                
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
                
                # Aggregate fraud data using hierarchical parameters
                aggregated = await self._aggregate_fraud_data(
                    db, survey_id, platform_id=platform_id, respondent_id=respondent_id,
                    date_from=date_from_dt, date_to=date_to_dt
                )
                
                logger.info(f"Respondent fraud summary generated for {survey_id}/{platform_id}/{respondent_id}")
                
                return {
                    "survey_id": survey_id,
                    "platform_id": platform_id,
                    "respondent_id": respondent_id,
                    **aggregated
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting respondent fraud summary: {e}")
                raise HTTPException(status_code=500, detail="Failed to get respondent fraud summary")
        
        @self.router.get("/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/fraud")
        async def get_session_fraud_hierarchical(
            survey_id: str,
            platform_id: str,
            respondent_id: str,
            session_id: str,
            db: AsyncSession = Depends(get_db)
        ):
            """Get fraud detection data for a session via hierarchical path."""
            try:
                # Verify session belongs to this hierarchy
                session_query = select(Session).where(
                    and_(
                        Session.id == session_id,
                        Session.survey_id == survey_id,
                        Session.platform_id == platform_id,
                        Session.respondent_id == respondent_id
                    )
                )
                
                session_result = await db.execute(session_query)
                session = session_result.scalar_one_or_none()
                
                if not session:
                    raise HTTPException(
                        status_code=404,
                        detail="Session not found in the specified hierarchy"
                    )
                
                # Get latest fraud indicator
                fraud_query = (
                    select(FraudIndicator)
                    .where(FraudIndicator.session_id == session_id)
                    .order_by(FraudIndicator.created_at.desc())
                    .limit(1)
                )
                fraud_result = await db.execute(fraud_query)
                fraud_indicator = fraud_result.scalar_one_or_none()
                
                if not fraud_indicator:
                    return {
                        "survey_id": survey_id,
                        "platform_id": platform_id,
                        "respondent_id": respondent_id,
                        "session_id": session_id,
                        "fraud_analysis_available": False,
                        "message": "No fraud analysis has been performed for this session"
                    }
                
                # Format fraud indicator data
                return {
                    "survey_id": survey_id,
                    "platform_id": platform_id,
                    "respondent_id": respondent_id,
                    "session_id": session_id,
                    "fraud_analysis_available": True,
                    "overall_fraud_score": float(fraud_indicator.overall_fraud_score) if fraud_indicator.overall_fraud_score else None,
                    "is_duplicate": fraud_indicator.is_duplicate,
                    "fraud_confidence": float(fraud_indicator.fraud_confidence) if fraud_indicator.fraud_confidence else None,
                    "risk_level": fraud_indicator.risk_level,
                    "ip_analysis": {
                        "ip_address": fraud_indicator.ip_address,
                        "usage_count": fraud_indicator.ip_usage_count,
                        "sessions_today": fraud_indicator.ip_sessions_today,
                        "risk_score": float(fraud_indicator.ip_risk_score) if fraud_indicator.ip_risk_score else None
                    },
                    "device_fingerprint": {
                        "fingerprint": fraud_indicator.device_fingerprint,
                        "usage_count": fraud_indicator.fingerprint_usage_count,
                        "risk_score": float(fraud_indicator.fingerprint_risk_score) if fraud_indicator.fingerprint_risk_score else None
                    },
                    "duplicate_responses": {
                        "similarity_score": float(fraud_indicator.response_similarity_score) if fraud_indicator.response_similarity_score else None,
                        "duplicate_count": fraud_indicator.duplicate_response_count
                    },
                    "geolocation": {
                        "consistent": fraud_indicator.geolocation_consistent,
                        "risk_score": float(fraud_indicator.geolocation_risk_score) if fraud_indicator.geolocation_risk_score else None
                    },
                    "velocity": {
                        "responses_per_hour": float(fraud_indicator.responses_per_hour) if fraud_indicator.responses_per_hour else None,
                        "risk_score": float(fraud_indicator.velocity_risk_score) if fraud_indicator.velocity_risk_score else None
                    },
                    "flag_reasons": fraud_indicator.flag_reasons,
                    "created_at": fraud_indicator.created_at.isoformat() if fraud_indicator.created_at else None
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting session fraud data: {e}")
                raise HTTPException(status_code=500, detail="Failed to get session fraud data")
        
        # Grid Analysis Endpoints
        
        @self.router.get("/{survey_id}/grid-analysis/summary")
        async def get_survey_grid_analysis_summary(
            survey_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get grid analysis summary for a survey."""
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
                
                # Get grid analysis summary
                summary = await self.aggregation_service.get_grid_analysis_summary(
                    survey_id, None, None, None, db, date_from=date_from_dt, date_to=date_to_dt
                )
                
                logger.info(f"Survey grid analysis summary generated for {survey_id}")
                
                return summary
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting survey grid analysis summary: {e}")
                raise HTTPException(status_code=500, detail="Failed to get survey grid analysis summary")
        
        @self.router.get("/{survey_id}/platforms/{platform_id}/grid-analysis/summary")
        async def get_platform_grid_analysis_summary(
            survey_id: str,
            platform_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get grid analysis summary for a platform within a survey."""
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
                
                # Get grid analysis summary
                summary = await self.aggregation_service.get_grid_analysis_summary(
                    survey_id, platform_id, None, None, db, date_from=date_from_dt, date_to=date_to_dt
                )
                
                logger.info(f"Platform grid analysis summary generated for {survey_id}/{platform_id}")
                
                return summary
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting platform grid analysis summary: {e}")
                raise HTTPException(status_code=500, detail="Failed to get platform grid analysis summary")
        
        @self.router.get("/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/grid-analysis/summary")
        async def get_respondent_grid_analysis_summary(
            survey_id: str,
            platform_id: str,
            respondent_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get grid analysis summary for a respondent within a platform."""
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
                
                # Get grid analysis summary
                summary = await self.aggregation_service.get_grid_analysis_summary(
                    survey_id, platform_id, respondent_id, None, db, date_from=date_from_dt, date_to=date_to_dt
                )
                
                logger.info(f"Respondent grid analysis summary generated for {survey_id}/{platform_id}/{respondent_id}")
                
                return summary
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting respondent grid analysis summary: {e}")
                raise HTTPException(status_code=500, detail="Failed to get respondent grid analysis summary")
        
        @self.router.get("/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/grid-analysis")
        async def get_session_grid_analysis(
            survey_id: str,
            platform_id: str,
            respondent_id: str,
            session_id: str,
            db: AsyncSession = Depends(get_db)
        ):
            """Get grid analysis for a specific session."""
            try:
                # Verify session belongs to hierarchy
                session_query = select(Session).where(
                    and_(
                        Session.id == session_id,
                        Session.survey_id == survey_id,
                        Session.platform_id == platform_id,
                        Session.respondent_id == respondent_id
                    )
                )
                session_result = await db.execute(session_query)
                session = session_result.scalar_one_or_none()
                
                if not session:
                    raise HTTPException(
                        status_code=404,
                        detail="Session not found in the specified hierarchy"
                    )
                
                # Get grid analysis summary for this session
                summary = await self.aggregation_service.get_grid_analysis_summary(
                    survey_id, platform_id, respondent_id, session_id, db
                )
                
                logger.info(f"Session grid analysis generated for {session_id}")
                
                return summary
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting session grid analysis: {e}")
                raise HTTPException(status_code=500, detail="Failed to get session grid analysis")
        
        # Timing Analysis Endpoints
        
        @self.router.get("/{survey_id}/timing-analysis/summary")
        async def get_survey_timing_analysis_summary(
            survey_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get timing analysis summary for a survey."""
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
                
                # Get timing analysis summary
                summary = await self.aggregation_service.get_timing_analysis_summary(
                    survey_id, None, None, None, db, date_from=date_from_dt, date_to=date_to_dt
                )
                
                logger.info(f"Survey timing analysis summary generated for {survey_id}")
                
                return summary
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting survey timing analysis summary: {e}")
                raise HTTPException(status_code=500, detail="Failed to get survey timing analysis summary")
        
        @self.router.get("/{survey_id}/platforms/{platform_id}/timing-analysis/summary")
        async def get_platform_timing_analysis_summary(
            survey_id: str,
            platform_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get timing analysis summary for a platform within a survey."""
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
                
                # Get timing analysis summary
                summary = await self.aggregation_service.get_timing_analysis_summary(
                    survey_id, platform_id, None, None, db, date_from=date_from_dt, date_to=date_to_dt
                )
                
                logger.info(f"Platform timing analysis summary generated for {survey_id}/{platform_id}")
                
                return summary
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting platform timing analysis summary: {e}")
                raise HTTPException(status_code=500, detail="Failed to get platform timing analysis summary")
        
        @self.router.get("/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/timing-analysis/summary")
        async def get_respondent_timing_analysis_summary(
            survey_id: str,
            platform_id: str,
            respondent_id: str,
            date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
            date_to: Optional[str] = Query(None, description="End date (ISO format)"),
            db: AsyncSession = Depends(get_db)
        ):
            """Get timing analysis summary for a respondent within a platform."""
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
                
                # Get timing analysis summary
                summary = await self.aggregation_service.get_timing_analysis_summary(
                    survey_id, platform_id, respondent_id, None, db, date_from=date_from_dt, date_to=date_to_dt
                )
                
                logger.info(f"Respondent timing analysis summary generated for {survey_id}/{platform_id}/{respondent_id}")
                
                return summary
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting respondent timing analysis summary: {e}")
                raise HTTPException(status_code=500, detail="Failed to get respondent timing analysis summary")
        
        @self.router.get("/{survey_id}/platforms/{platform_id}/respondents/{respondent_id}/sessions/{session_id}/timing-analysis")
        async def get_session_timing_analysis(
            survey_id: str,
            platform_id: str,
            respondent_id: str,
            session_id: str,
            db: AsyncSession = Depends(get_db)
        ):
            """Get timing analysis for a specific session."""
            try:
                # Verify session belongs to hierarchy
                session_query = select(Session).where(
                    and_(
                        Session.id == session_id,
                        Session.survey_id == survey_id,
                        Session.platform_id == platform_id,
                        Session.respondent_id == respondent_id
                    )
                )
                session_result = await db.execute(session_query)
                session = session_result.scalar_one_or_none()
                
                if not session:
                    raise HTTPException(
                        status_code=404,
                        detail="Session not found in the specified hierarchy"
                    )
                
                # Get timing analysis summary for this session
                summary = await self.aggregation_service.get_timing_analysis_summary(
                    survey_id, platform_id, respondent_id, session_id, db
                )
                
                logger.info(f"Session timing analysis generated for {session_id}")
                
                return summary
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting session timing analysis: {e}")
                raise HTTPException(status_code=500, detail="Failed to get session timing analysis")
    
    async def _aggregate_fraud_data(
        self,
        db: AsyncSession,
        survey_id: str,
        platform_id: Optional[str] = None,
        respondent_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Aggregate fraud detection metrics from fraud indicators.
        
        Uses denormalized hierarchical fields in fraud_indicators for efficient queries.
        """
        try:
            # Build fraud indicator query using denormalized hierarchical fields
            fraud_conditions = [FraudIndicator.survey_id == survey_id]
            
            if platform_id:
                fraud_conditions.append(FraudIndicator.platform_id == platform_id)
            
            if respondent_id:
                fraud_conditions.append(FraudIndicator.respondent_id == respondent_id)
            
            # Add date filters
            if date_from:
                fraud_conditions.append(FraudIndicator.created_at >= date_from)
            if date_to:
                fraud_conditions.append(FraudIndicator.created_at <= date_to)
            
            fraud_query = select(FraudIndicator).where(and_(*fraud_conditions))
            fraud_result = await db.execute(fraud_query)
            fraud_indicators = fraud_result.scalars().all()
            
            # Get total sessions count for this hierarchy (even without fraud analysis)
            session_conditions = [Session.survey_id == survey_id]
            if platform_id:
                session_conditions.append(Session.platform_id == platform_id)
            if respondent_id:
                session_conditions.append(Session.respondent_id == respondent_id)
            
            session_count_query = select(func.count(Session.id)).where(and_(*session_conditions))
            session_count_result = await db.execute(session_count_query)
            total_sessions = session_count_result.scalar() or 0
            
            if not fraud_indicators:
                return {
                    "total_sessions_analyzed": 0,
                    "total_sessions": total_sessions,
                    "duplicate_sessions": 0,
                    "high_risk_sessions": 0,
                    "average_fraud_score": None,
                    "duplicate_rate": 0.0,
                    "high_risk_rate": 0.0,
                    "risk_distribution": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
                    "fraud_methods": {
                        "ip_high_risk": 0,
                        "fingerprint_high_risk": 0,
                        "duplicate_responses": 0,
                        "geolocation_inconsistent": 0,
                        "high_velocity": 0
                    }
                }
            
            # Calculate aggregate statistics
            total_analyzed = len(fraud_indicators)
            duplicate_count = sum(1 for fi in fraud_indicators if fi.is_duplicate)
            
            # Calculate risk distribution
            risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
            high_risk_count = 0
            fraud_scores = []
            
            # Count fraud method flags
            fraud_methods = {
                "ip_high_risk": 0,
                "fingerprint_high_risk": 0,
                "duplicate_responses": 0,
                "geolocation_inconsistent": 0,
                "high_velocity": 0
            }
            
            for fi in fraud_indicators:
                # Risk level distribution
                risk_level = fi.risk_level
                if risk_level in risk_distribution:
                    risk_distribution[risk_level] += 1
                
                # High risk count (score >= 0.7)
                if fi.overall_fraud_score and float(fi.overall_fraud_score) >= 0.7:
                    high_risk_count += 1
                
                # Collect fraud scores
                if fi.overall_fraud_score:
                    fraud_scores.append(float(fi.overall_fraud_score))
                
                # Count fraud method flags
                if fi.flag_reasons:
                    if "ip_reuse" in fi.flag_reasons:
                        fraud_methods["ip_high_risk"] += 1
                    if "device_reuse" in fi.flag_reasons:
                        fraud_methods["fingerprint_high_risk"] += 1
                    if "duplicate_responses" in fi.flag_reasons:
                        fraud_methods["duplicate_responses"] += 1
                    if "geolocation_inconsistency" in fi.flag_reasons:
                        fraud_methods["geolocation_inconsistent"] += 1
                    if "high_velocity" in fi.flag_reasons:
                        fraud_methods["high_velocity"] += 1
            
            # Calculate average fraud score
            avg_fraud_score = sum(fraud_scores) / len(fraud_scores) if fraud_scores else None
            
            # Calculate rates
            duplicate_rate = (duplicate_count / total_analyzed * 100) if total_analyzed > 0 else 0.0
            high_risk_rate = (high_risk_count / total_analyzed * 100) if total_analyzed > 0 else 0.0
            
            return {
                "total_sessions_analyzed": total_analyzed,
                "total_sessions": total_sessions,
                "duplicate_sessions": duplicate_count,
                "high_risk_sessions": high_risk_count,
                "average_fraud_score": round(avg_fraud_score, 3) if avg_fraud_score else None,
                "duplicate_rate": round(duplicate_rate, 2),
                "high_risk_rate": round(high_risk_rate, 2),
                "risk_distribution": risk_distribution,
                "fraud_methods": fraud_methods
            }
            
        except Exception as e:
            logger.error(f"Error aggregating fraud data: {e}")
            raise
    
    async def _aggregate_text_analysis(self, responses: List[SurveyResponse]) -> Dict[str, Any]:
        """Aggregate text analysis metrics from a list of responses."""
        if not responses:
            return {
                "total_responses": 0,
                "avg_quality_score": None,
                "flagged_count": 0,
                "flagged_percentage": 0.0,
                "flag_type_counts": {},
                "quality_distribution": {}
            }
        
        total_responses = len(responses)
        quality_scores = [r.quality_score for r in responses if r.quality_score is not None]
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else None
        flagged_count = sum(1 for r in responses if r.is_flagged)
        flagged_percentage = (flagged_count / total_responses * 100) if total_responses > 0 else 0
        
        # Count flag types
        flag_type_counts = {}
        for response in responses:
            if response.flag_reasons:
                for flag_type in response.flag_reasons.keys():
                    flag_type_counts[flag_type] = flag_type_counts.get(flag_type, 0) + 1
        
        # Calculate quality distribution (0-10, 10-20, ..., 90-100)
        quality_distribution = {}
        for i in range(10):
            bucket_start = i * 10
            bucket_end = (i + 1) * 10
            count = sum(1 for score in quality_scores if bucket_start <= score < bucket_end)
            quality_distribution[f"{bucket_start}-{bucket_end}"] = count
        
        return {
            "total_responses": total_responses,
            "avg_quality_score": round(avg_quality_score, 2) if avg_quality_score is not None else None,
            "flagged_count": flagged_count,
            "flagged_percentage": round(flagged_percentage, 2),
            "flag_type_counts": flag_type_counts,
            "quality_distribution": quality_distribution
        }

