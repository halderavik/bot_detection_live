"""
Dashboard controller for analytics and metrics endpoints.

This module handles HTTP requests related to dashboard analytics,
metrics, and reporting functionality.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel

from database.database import get_db
from models.session import Session as SessionModel
from models.behavior_data import BehaviorData
from models.detection_result import DetectionResult
from utils.logger import get_logger
from utils.helpers import format_success_response

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# Pydantic models for response validation
class MetricsSummary(BaseModel):
    """Summary metrics for dashboard."""
    total_sessions: int
    active_sessions: int
    bot_sessions: int
    human_sessions: int
    total_events: int
    avg_processing_time_ms: float
    detection_rate: float


class TimeSeriesData(BaseModel):
    """Time series data for charts."""
    timestamp: str
    sessions: int
    events: int
    bot_detections: int


class EventTypeBreakdown(BaseModel):
    """Event type breakdown for analytics."""
    event_type: str
    count: int
    percentage: float


@router.get("/metrics/summary")
async def get_metrics_summary(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db)
):
    """
    Get summary metrics for the dashboard.
    
    Args:
        start_date: Start date filter
        end_date: End date filter
        db: Database session
        
    Returns:
        Summary metrics
    """
    try:
        # Build date filter
        date_filter = []
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                date_filter.append(SessionModel.created_at >= start_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                date_filter.append(SessionModel.created_at <= end_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        
        # Get session metrics
        session_query = db.query(SessionModel)
        if date_filter:
            session_query = session_query.filter(and_(*date_filter))
        
        total_sessions = session_query.count()
        active_sessions = session_query.filter(SessionModel.is_active == True).count()
        bot_sessions = session_query.filter(SessionModel.is_bot == True).count()
        human_sessions = session_query.filter(SessionModel.is_bot == False).count()
        
        # Get event metrics
        event_query = db.query(BehaviorData)
        if date_filter:
            event_query = event_query.join(SessionModel).filter(and_(*date_filter))
        
        total_events = event_query.count()
        
        # Get average processing time
        result_query = db.query(func.avg(DetectionResult.processing_time_ms))
        if date_filter:
            result_query = result_query.join(SessionModel).filter(and_(*date_filter))
        
        avg_processing_time = result_query.scalar() or 0.0
        
        # Calculate detection rate
        detection_rate = (bot_sessions / total_sessions * 100) if total_sessions > 0 else 0.0
        
        return MetricsSummary(
            total_sessions=total_sessions,
            active_sessions=active_sessions,
            bot_sessions=bot_sessions,
            human_sessions=human_sessions,
            total_events=total_events,
            avg_processing_time_ms=round(avg_processing_time, 2),
            detection_rate=round(detection_rate, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics summary")


@router.get("/metrics/timeseries")
async def get_timeseries_data(
    interval: str = Query("hour", description="Time interval (hour, day, week)"),
    days: int = Query(7, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """
    Get time series data for charts.
    
    Args:
        interval: Time interval for grouping
        days: Number of days to look back
        db: Database session
        
    Returns:
        Time series data
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Validate interval
        if interval not in ["hour", "day", "week"]:
            raise HTTPException(status_code=400, detail="Invalid interval")
        
        # Build time series query based on interval
        if interval == "hour":
            time_format = func.date_trunc('hour', SessionModel.created_at)
        elif interval == "day":
            time_format = func.date_trunc('day', SessionModel.created_at)
        else:  # week
            time_format = func.date_trunc('week', SessionModel.created_at)
        
        # Get session counts by time
        session_counts = db.query(
            time_format.label('timestamp'),
            func.count(SessionModel.id).label('sessions')
        ).filter(
            SessionModel.created_at >= start_date,
            SessionModel.created_at <= end_date
        ).group_by(time_format).order_by(time_format).all()
        
        # Get event counts by time
        event_counts = db.query(
            time_format.label('timestamp'),
            func.count(BehaviorData.id).label('events')
        ).join(SessionModel).filter(
            SessionModel.created_at >= start_date,
            SessionModel.created_at <= end_date
        ).group_by(time_format).order_by(time_format).all()
        
        # Get bot detection counts by time
        bot_counts = db.query(
            time_format.label('timestamp'),
            func.count(DetectionResult.id).label('bot_detections')
        ).join(SessionModel).filter(
            and_(
                SessionModel.created_at >= start_date,
                SessionModel.created_at <= end_date,
                DetectionResult.is_bot == True
            )
        ).group_by(time_format).order_by(time_format).all()
        
        # Combine data
        timeseries_data = []
        for session_count in session_counts:
            timestamp = session_count.timestamp.isoformat()
            events = next((e.events for e in event_counts if e.timestamp == session_count.timestamp), 0)
            bot_detections = next((b.bot_detections for b in bot_counts if b.timestamp == session_count.timestamp), 0)
            
            timeseries_data.append(TimeSeriesData(
                timestamp=timestamp,
                sessions=session_count.sessions,
                events=events,
                bot_detections=bot_detections
            ))
        
        return format_success_response(
            data=timeseries_data,
            message=f"Retrieved {len(timeseries_data)} time series data points"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get time series data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get time series data")


@router.get("/metrics/event-breakdown")
async def get_event_breakdown(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db)
):
    """
    Get breakdown of events by type.
    
    Args:
        start_date: Start date filter
        end_date: End date filter
        db: Database session
        
    Returns:
        Event type breakdown
    """
    try:
        # Build date filter
        date_filter = []
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                date_filter.append(SessionModel.created_at >= start_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                date_filter.append(SessionModel.created_at <= end_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        
        # Get event counts by type
        query = db.query(
            BehaviorData.event_type,
            func.count(BehaviorData.id).label('count')
        ).join(SessionModel)
        
        if date_filter:
            query = query.filter(and_(*date_filter))
        
        event_counts = query.group_by(BehaviorData.event_type).all()
        
        # Calculate total for percentages
        total_events = sum(count.count for count in event_counts)
        
        # Build breakdown
        breakdown = []
        for event_count in event_counts:
            percentage = (event_count.count / total_events * 100) if total_events > 0 else 0
            breakdown.append(EventTypeBreakdown(
                event_type=event_count.event_type,
                count=event_count.count,
                percentage=round(percentage, 2)
            ))
        
        # Sort by count descending
        breakdown.sort(key=lambda x: x.count, reverse=True)
        
        return format_success_response(
            data=breakdown,
            message=f"Retrieved breakdown for {len(breakdown)} event types"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get event breakdown: {e}")
        raise HTTPException(status_code=500, detail="Failed to get event breakdown")


@router.get("/sessions/recent")
async def get_recent_sessions(
    limit: int = Query(10, description="Number of recent sessions to return"),
    db: Session = Depends(get_db)
):
    """
    Get recent sessions for dashboard.
    
    Args:
        limit: Number of sessions to return
        db: Database session
        
    Returns:
        Recent sessions
    """
    try:
        sessions = db.query(SessionModel).order_by(
            SessionModel.created_at.desc()
        ).limit(limit).all()
        
        session_data = []
        for session in sessions:
            # Get event count
            event_count = db.query(BehaviorData).filter(
                BehaviorData.session_id == session.id
            ).count()
            
            # Get latest result
            latest_result = db.query(DetectionResult).filter(
                DetectionResult.session_id == session.id
            ).order_by(DetectionResult.created_at.desc()).first()
            
            session_data.append({
                "id": session.id,
                "user_agent": session.user_agent,
                "ip_address": session.ip_address,
                "is_active": session.is_active,
                "is_bot": session.is_bot,
                "event_count": event_count,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "last_activity": session.last_activity.isoformat() if session.last_activity else None,
                "latest_result": latest_result.to_dict() if latest_result else None
            })
        
        return format_success_response(
            data=session_data,
            message=f"Retrieved {len(session_data)} recent sessions"
        )
        
    except Exception as e:
        logger.error(f"Failed to get recent sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent sessions")


@router.get("/sessions/top-bots")
async def get_top_bot_sessions(
    limit: int = Query(10, description="Number of top bot sessions to return"),
    db: Session = Depends(get_db)
):
    """
    Get sessions with highest bot scores.
    
    Args:
        limit: Number of sessions to return
        db: Database session
        
    Returns:
        Top bot sessions
    """
    try:
        # Get sessions with highest bot scores
        top_results = db.query(DetectionResult).filter(
            DetectionResult.is_bot == True
        ).order_by(
            DetectionResult.bot_score.desc()
        ).limit(limit).all()
        
        session_data = []
        for result in top_results:
            session = db.query(SessionModel).filter(
                SessionModel.id == result.session_id
            ).first()
            
            if session:
                session_data.append({
                    "session_id": result.session_id,
                    "bot_score": result.bot_score,
                    "confidence": result.confidence,
                    "event_count": result.event_count,
                    "processing_time_ms": result.processing_time_ms,
                    "created_at": result.created_at.isoformat() if result.created_at else None,
                    "user_agent": session.user_agent,
                    "ip_address": session.ip_address
                })
        
        return format_success_response(
            data=session_data,
            message=f"Retrieved {len(session_data)} top bot sessions"
        )
        
    except Exception as e:
        logger.error(f"Failed to get top bot sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get top bot sessions")


@router.get("/performance/stats")
async def get_performance_stats(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db)
):
    """
    Get performance statistics.
    
    Args:
        start_date: Start date filter
        end_date: End date filter
        db: Database session
        
    Returns:
        Performance statistics
    """
    try:
        # Build date filter
        date_filter = []
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                date_filter.append(DetectionResult.created_at >= start_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                date_filter.append(DetectionResult.created_at <= end_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        
        # Get performance metrics
        query = db.query(DetectionResult)
        if date_filter:
            query = query.filter(and_(*date_filter))
        
        # Calculate statistics
        total_results = query.count()
        avg_processing_time = query.with_entities(
            func.avg(DetectionResult.processing_time_ms)
        ).scalar() or 0.0
        
        min_processing_time = query.with_entities(
            func.min(DetectionResult.processing_time_ms)
        ).scalar() or 0.0
        
        max_processing_time = query.with_entities(
            func.max(DetectionResult.processing_time_ms)
        ).scalar() or 0.0
        
        avg_confidence = query.with_entities(
            func.avg(DetectionResult.confidence)
        ).scalar() or 0.0
        
        # Get event count statistics
        avg_events = query.with_entities(
            func.avg(DetectionResult.event_count)
        ).scalar() or 0.0
        
        return format_success_response(
            data={
                "total_analyses": total_results,
                "avg_processing_time_ms": round(avg_processing_time, 2),
                "min_processing_time_ms": round(min_processing_time, 2),
                "max_processing_time_ms": round(max_processing_time, 2),
                "avg_confidence": round(avg_confidence, 3),
                "avg_events_per_analysis": round(avg_events, 1)
            },
            message="Performance statistics retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance stats") 