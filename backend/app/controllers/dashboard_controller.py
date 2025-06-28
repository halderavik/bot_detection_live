"""
Dashboard Controller.

This controller handles dashboard and analytics endpoints for viewing
bot detection statistics, session analytics, and reporting data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models import Session, BehaviorData, DetectionResult
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class DashboardController:
    """Controller for dashboard and analytics endpoints."""
    
    def __init__(self):
        """Initialize the dashboard controller."""
        self.router = APIRouter(prefix="/dashboard", tags=["dashboard"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes for dashboard endpoints."""
        
        @self.router.get("/overview")
        async def get_overview_stats(
            db: AsyncSession = Depends(get_db),
            days: int = Query(7, description="Number of days to analyze")
        ):
            """Get overview statistics for the dashboard."""
            try:
                # Calculate date range
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
                
                # Get session statistics
                session_stats = await self._get_session_stats(db, start_date, end_date)
                
                # Get detection statistics
                detection_stats = await self._get_detection_stats(db, start_date, end_date)
                
                # Get event statistics
                event_stats = await self._get_event_stats(db, start_date, end_date)
                
                # Get platform distribution
                platform_stats = await self._get_platform_stats(db, start_date, end_date)
                
                return {
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "days": days
                    },
                    "sessions": session_stats,
                    "detections": detection_stats,
                    "events": event_stats,
                    "platforms": platform_stats
                }
                
            except Exception as e:
                logger.error(f"Error getting overview stats: {e}")
                raise HTTPException(status_code=500, detail="Failed to get overview statistics")
        
        @self.router.get("/sessions")
        async def get_sessions_list(
            db: AsyncSession = Depends(get_db),
            page: int = Query(1, ge=1, description="Page number"),
            limit: int = Query(50, ge=1, le=100, description="Items per page"),
            platform: Optional[str] = Query(None, description="Filter by platform"),
            risk_level: Optional[str] = Query(None, description="Filter by risk level"),
            is_bot: Optional[bool] = Query(None, description="Filter by bot detection")
        ):
            """Get paginated list of sessions with filters."""
            try:
                # Test basic import and model access
                logger.info(f"Session model: {Session}")
                logger.info(f"Session table name: {Session.__tablename__}")
                
                # Simple count query first
                count_result = await db.execute(select(func.count(Session.id)))
                total_count = count_result.scalar()
                logger.info(f"Total sessions in database: {total_count}")
                
                # Simple query with eager loading of behavior_data
                query = select(Session).options(selectinload(Session.behavior_data))
                
                # Apply filters
                if platform:
                    query = query.where(Session.platform == platform)
                
                # Apply pagination
                offset = (page - 1) * limit
                query = query.offset(offset).limit(limit)
                
                # Execute query
                result = await db.execute(query)
                sessions = result.scalars().all()
                logger.info(f"Retrieved {len(sessions)} sessions")
                
                # Format response with minimal data
                sessions_data = []
                for session in sessions:
                    session_data = {
                        "id": session.id,
                        "created_at": session.created_at.isoformat(),
                        "last_activity": session.last_activity.isoformat(),
                        "is_active": session.is_active,
                        "platform": session.platform,
                        "survey_id": session.survey_id,
                        "respondent_id": session.respondent_id,
                        "event_count": len(session.behavior_data) if session.behavior_data else 0
                    }
                    sessions_data.append(session_data)
                
                return {
                    "sessions": sessions_data,
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": total_count,
                        "pages": (total_count + limit - 1) // limit
                    }
                }
                
            except Exception as e:
                logger.error(f"Error getting sessions list: {e}")
                logger.error(f"Error type: {type(e)}")
                logger.error(f"Error details: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise HTTPException(status_code=500, detail="Failed to get sessions list")
        
        @self.router.get("/sessions/{session_id}/details")
        async def get_session_details(
            session_id: str,
            db: AsyncSession = Depends(get_db)
        ):
            """Get detailed information about a specific session."""
            try:
                # Get session with all related data
                query = (
                    select(Session)
                    .options(
                        selectinload(Session.behavior_data),
                        selectinload(Session.detection_results)
                    )
                    .where(Session.id == session_id)
                )
                
                result = await db.execute(query)
                session = result.scalar_one_or_none()
                
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                # Format behavior data
                behavior_data = []
                for event in session.behavior_data:
                    behavior_data.append({
                        "id": event.id,
                        "event_type": event.event_type,
                        "timestamp": event.timestamp.isoformat(),
                        "element_id": event.element_id,
                        "element_type": event.element_type,
                        "page_url": event.page_url,
                        "screen_width": event.screen_width,
                        "screen_height": event.screen_height
                    })
                
                # Format detection results
                detection_results = []
                for detection in session.detection_results:
                    detection_results.append({
                        "id": detection.id,
                        "is_bot": detection.is_bot,
                        "confidence_score": detection.confidence_score,
                        "risk_level": detection.risk_level,
                        "processing_time_ms": detection.processing_time_ms,
                        "event_count": detection.event_count,
                        "analysis_summary": detection.analysis_summary,
                        "method_scores": detection.method_scores,
                        "flagged_patterns": detection.flagged_patterns,
                        "analyzed_at": detection.analyzed_at.isoformat()
                    })
                
                return {
                    "session": {
                        "id": session.id,
                        "created_at": session.created_at.isoformat(),
                        "last_activity": session.last_activity.isoformat(),
                        "is_active": session.is_active,
                        "is_completed": session.is_completed,
                        "user_agent": session.user_agent,
                        "ip_address": session.ip_address,
                        "referrer": session.referrer,
                        "platform": session.platform,
                        "survey_id": session.survey_id,
                        "respondent_id": session.respondent_id
                    },
                    "behavior_data": behavior_data,
                    "detection_results": detection_results,
                    "statistics": {
                        "total_events": len(session.behavior_data),
                        "total_detections": len(session.detection_results),
                        "session_duration_minutes": (
                            (session.last_activity - session.created_at).total_seconds() / 60
                        ) if session.last_activity else 0
                    }
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting session details: {e}")
                raise HTTPException(status_code=500, detail="Failed to get session details")
        
        @self.router.get("/analytics/trends")
        async def get_analytics_trends(
            db: AsyncSession = Depends(get_db),
            days: int = Query(30, description="Number of days to analyze"),
            interval: str = Query("day", description="Time interval: day, hour")
        ):
            """Get analytics trends over time."""
            try:
                # Calculate date range
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
                
                # Get daily/hourly trends
                trends = await self._get_trends_data(db, start_date, end_date, interval)
                
                return {
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "interval": interval
                    },
                    "trends": trends
                }
                
            except Exception as e:
                logger.error(f"Error getting analytics trends: {e}")
                raise HTTPException(status_code=500, detail="Failed to get analytics trends")
        
        @self.router.get("/test")
        async def test_endpoint(db: AsyncSession = Depends(get_db)):
            """Test endpoint to check database connectivity."""
            try:
                # Simple count query
                result = await db.execute(select(func.count(Session.id)))
                count = result.scalar()
                return {"message": "Database connection works", "session_count": count}
            except Exception as e:
                logger.error(f"Test endpoint error: {e}")
                return {"error": str(e)}
    
    async def _get_session_stats(self, db: AsyncSession, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get session statistics for the given period."""
        # Total sessions
        total_query = select(func.count(Session.id)).where(
            and_(Session.created_at >= start_date, Session.created_at <= end_date)
        )
        total_result = await db.execute(total_query)
        total_sessions = total_result.scalar()
        
        # Active sessions
        active_query = select(func.count(Session.id)).where(
            and_(
                Session.created_at >= start_date,
                Session.created_at <= end_date,
                Session.is_active == True
            )
        )
        active_result = await db.execute(active_query)
        active_sessions = active_result.scalar()
        
        # Completed sessions
        completed_query = select(func.count(Session.id)).where(
            and_(
                Session.created_at >= start_date,
                Session.created_at <= end_date,
                Session.is_completed == True
            )
        )
        completed_result = await db.execute(completed_query)
        completed_sessions = completed_result.scalar()
        
        return {
            "total": total_sessions,
            "active": active_sessions,
            "completed": completed_sessions,
            "completion_rate": (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        }
    
    async def _get_detection_stats(self, db: AsyncSession, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get detection statistics for the given period."""
        # Total detections
        total_query = select(func.count(DetectionResult.id)).where(
            and_(DetectionResult.created_at >= start_date, DetectionResult.created_at <= end_date)
        )
        total_result = await db.execute(total_query)
        total_detections = total_result.scalar()
        
        # Bot detections
        bot_query = select(func.count(DetectionResult.id)).where(
            and_(
                DetectionResult.created_at >= start_date,
                DetectionResult.created_at <= end_date,
                DetectionResult.is_bot == True
            )
        )
        bot_result = await db.execute(bot_query)
        bot_detections = bot_result.scalar()
        
        # High confidence detections
        high_conf_query = select(func.count(DetectionResult.id)).where(
            and_(
                DetectionResult.created_at >= start_date,
                DetectionResult.created_at <= end_date,
                DetectionResult.confidence_score >= 0.8
            )
        )
        high_conf_result = await db.execute(high_conf_query)
        high_conf_detections = high_conf_result.scalar()
        
        return {
            "total": total_detections,
            "bots_detected": bot_detections,
            "high_confidence": high_conf_detections,
            "bot_rate": (bot_detections / total_detections * 100) if total_detections > 0 else 0
        }
    
    async def _get_event_stats(self, db: AsyncSession, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get event statistics for the given period."""
        # Total events
        total_query = select(func.count(BehaviorData.id)).where(
            and_(BehaviorData.created_at >= start_date, BehaviorData.created_at <= end_date)
        )
        total_result = await db.execute(total_query)
        total_events = total_result.scalar()
        
        # Events by type
        type_query = (
            select(BehaviorData.event_type, func.count(BehaviorData.id))
            .where(and_(BehaviorData.created_at >= start_date, BehaviorData.created_at <= end_date))
            .group_by(BehaviorData.event_type)
        )
        type_result = await db.execute(type_query)
        events_by_type = dict(type_result.all())
        
        return {
            "total": total_events,
            "by_type": events_by_type
        }
    
    async def _get_platform_stats(self, db: AsyncSession, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get platform distribution statistics."""
        platform_query = (
            select(Session.platform, func.count(Session.id))
            .where(and_(Session.created_at >= start_date, Session.created_at <= end_date))
            .group_by(Session.platform)
        )
        platform_result = await db.execute(platform_query)
        platform_stats = dict(platform_result.all())
        
        return platform_stats
    
    async def _get_trends_data(self, db: AsyncSession, start_date: datetime, end_date: datetime, interval: str) -> List[Dict[str, Any]]:
        """Get trends data for the specified interval."""
        # This is a simplified implementation
        # In a real application, you'd use more sophisticated date grouping
        trends = []
        
        # For now, return daily trends
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            
            # Get sessions for this day
            session_query = select(func.count(Session.id)).where(
                and_(Session.created_at >= current_date, Session.created_at < next_date)
            )
            session_result = await db.execute(session_query)
            sessions_count = session_result.scalar()
            
            # Get detections for this day
            detection_query = select(func.count(DetectionResult.id)).where(
                and_(DetectionResult.created_at >= current_date, DetectionResult.created_at < next_date)
            )
            detection_result = await db.execute(detection_query)
            detections_count = detection_result.scalar()
            
            trends.append({
                "date": current_date.date().isoformat(),
                "sessions": sessions_count,
                "detections": detections_count
            })
            
            current_date = next_date
        
        return trends
    
    def get_router(self) -> APIRouter:
        """Get the router for this controller."""
        return self.router 