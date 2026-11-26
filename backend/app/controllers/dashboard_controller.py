"""
Dashboard Controller.

This controller handles dashboard and analytics endpoints for viewing
bot detection statistics, session analytics, and reporting data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
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
            platform: Optional[str] = Query(None, description="Filter by platform (platform or platform_id)"),
            risk_level: Optional[str] = Query(None, description="Filter by latest risk level; 'unknown' for not analysed"),
            is_bot: Optional[bool] = Query(None, description="Filter by latest bot verdict"),
            survey_id: Optional[str] = Query(None, description="Filter by survey id"),
            search: Optional[str] = Query(None, description="Session, respondent or survey id contains this text"),
        ):
            """Paginated sessions, newest first, each with its latest detection verdict."""
            try:
                # Exactly one latest detection per session, even when two share a timestamp.
                ranked = select(
                    DetectionResult,
                    func.row_number()
                    .over(
                        partition_by=DetectionResult.session_id,
                        order_by=(DetectionResult.analyzed_at.desc(), DetectionResult.created_at.desc(), DetectionResult.id.desc()),
                    )
                    .label("rank"),
                ).subquery()
                latest = select(ranked).where(ranked.c.rank == 1).subquery()
                events = (
                    select(BehaviorData.session_id, func.count(BehaviorData.id).label("n"))
                    .group_by(BehaviorData.session_id)
                    .subquery()
                )
                conditions = []
                if platform:
                    conditions.append(or_(Session.platform == platform, Session.platform_id == platform))
                if survey_id:
                    conditions.append(Session.survey_id == survey_id)
                if search:
                    like = f"%{search.strip()}%"
                    conditions.append(
                        or_(Session.id.ilike(like), Session.respondent_id.ilike(like), Session.survey_id.ilike(like))
                    )
                if is_bot is not None:
                    conditions.append(latest.c.is_bot == is_bot)
                if risk_level:
                    if risk_level.lower() == "unknown":
                        conditions.append(latest.c.id.is_(None))
                    else:
                        conditions.append(func.lower(latest.c.risk_level) == risk_level.lower())

                base = select(Session).outerjoin(latest, latest.c.session_id == Session.id)
                if conditions:
                    base = base.where(and_(*conditions))
                total_count = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0

                query = (
                    select(
                        Session,
                        latest.c.is_bot,
                        latest.c.risk_level,
                        latest.c.confidence_score,
                        latest.c.analyzed_at,
                        func.coalesce(events.c.n, 0),
                    )
                    .outerjoin(latest, latest.c.session_id == Session.id)
                    .outerjoin(events, events.c.session_id == Session.id)
                    .order_by(Session.created_at.desc())
                    .offset((page - 1) * limit)
                    .limit(limit)
                )
                if conditions:
                    query = query.where(and_(*conditions))
                rows = (await db.execute(query)).all()

                sessions_data = []
                for session, bot, risk, confidence, analyzed_at, event_count in rows:
                    sessions_data.append({
                        "id": session.id,
                        "created_at": session.created_at.isoformat(),
                        "last_activity": session.last_activity.isoformat(),
                        "is_active": session.is_active,
                        "platform": session.platform or session.platform_id,
                        "survey_id": session.survey_id,
                        "respondent_id": session.respondent_id,
                        "event_count": int(event_count or 0),
                        "analyzed": analyzed_at is not None,
                        "is_bot": bot,
                        "risk_level": (risk or "unknown").lower(),
                        "confidence_score": confidence,
                        "analyzed_at": analyzed_at.isoformat() if analyzed_at else None,
                    })

                return {
                    "sessions": sessions_data,
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": total_count,
                        "pages": (total_count + limit - 1) // limit,
                    },
                }
            except Exception as e:
                logger.error(f"Error getting sessions list: {e}")
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
                        "screen_height": event.screen_height,
                        "event_data": _event_extras(event.event_data),
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
                        "platform": session.platform or session.platform_id,
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
        """Detection statistics for sessions created in the period.

        Counts sessions, not detection rows, so a session analysed more than once counts
        once. ``bot_rate`` is bot sessions out of checked (analysed) sessions, the same
        rule the survey pages use.
        """
        in_period = and_(Session.created_at >= start_date, Session.created_at <= end_date)
        query = (
            select(
                func.count(func.distinct(DetectionResult.session_id)),
                func.count(func.distinct(case((DetectionResult.is_bot == True, DetectionResult.session_id)))),
                func.count(func.distinct(case((DetectionResult.confidence_score >= 0.8, DetectionResult.session_id)))),
            )
            .join(Session, DetectionResult.session_id == Session.id)
            .where(in_period)
        )
        checked, bots, high_confidence = (await db.execute(query)).one()
        checked, bots, high_confidence = checked or 0, bots or 0, high_confidence or 0
        return {
            "total": checked,
            "checked": checked,
            "bots_detected": bots,
            "high_confidence": high_confidence,
            "bot_rate": (bots / checked * 100) if checked > 0 else 0,
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
        """Sessions started per day, with how many of them were checked and judged bots.

        Counts are by the day the session started; ``detections`` is kept for older clients
        and equals ``checked``.
        """
        trends = []
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            in_day = and_(Session.created_at >= current_date, Session.created_at < next_date)
            sessions_count = (await db.execute(select(func.count(Session.id)).where(in_day))).scalar() or 0
            checked, bots = 0, 0
            if sessions_count:
                checked, bots = (
                    await db.execute(
                        select(
                            func.count(func.distinct(DetectionResult.session_id)),
                            func.count(func.distinct(case((DetectionResult.is_bot == True, DetectionResult.session_id)))),
                        )
                        .join(Session, DetectionResult.session_id == Session.id)
                        .where(in_day)
                    )
                ).one()
            trends.append({
                "date": current_date.date().isoformat(),
                "sessions": sessions_count,
                "checked": checked or 0,
                "bots": bots or 0,
                "detections": checked or 0,
            })
            current_date = next_date
        return trends
    
    def get_router(self) -> APIRouter:
        """Get the router for this controller."""
        return self.router 

# Fields already returned as columns (or not useful to clients) are left out of event_data.
_EVENT_COLUMNS = {
    "event_type", "timestamp", "element_id", "element_type", "element_class", "page_url", "page_title",
    "screen_width", "screen_height", "viewport_width", "viewport_height", "load_time", "response_time",
}


def _event_extras(data):
    """The event's own fields (coordinates, keys, scroll position, page timing...)."""
    if not isinstance(data, dict):
        return {}
    return {key: value for key, value in data.items() if key not in _EVENT_COLUMNS}
