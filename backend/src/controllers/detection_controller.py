"""
Detection controller for bot detection API endpoints.

This module handles HTTP requests related to bot detection operations
including session creation, data ingestion, and analysis.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.database import get_db
from models.session import Session as SessionModel
from models.behavior_data import BehaviorData
from models.detection_result import DetectionResult
from services.bot_detection_engine import BotDetectionEngine
from utils.logger import get_logger
from utils.helpers import (
    generate_session_id, generate_event_id, get_current_timestamp,
    calculate_processing_time, validate_event_data, extract_ip_from_headers,
    sanitize_user_agent, format_success_response, format_error_response
)

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/detection", tags=["detection"])

# Initialize bot detection engine
detection_engine = BotDetectionEngine()


# Pydantic models for request/response validation
class CreateSessionRequest(BaseModel):
    """Request model for creating a new session."""
    user_agent: Optional[str] = None
    referrer: Optional[str] = None


class CreateSessionResponse(BaseModel):
    """Response model for session creation."""
    session_id: str
    message: str


class IngestDataRequest(BaseModel):
    """Request model for ingesting behavior data."""
    events: List[Dict[str, Any]]


class IngestDataResponse(BaseModel):
    """Response model for data ingestion."""
    session_id: str
    events_processed: int
    bot_score: Optional[float] = None
    confidence: Optional[float] = None
    is_bot: Optional[bool] = None
    processing_time_ms: float


class SessionStatusResponse(BaseModel):
    """Response model for session status."""
    session_id: str
    is_active: bool
    is_bot: Optional[bool]
    event_count: int
    last_activity: str
    latest_result: Optional[Dict[str, Any]] = None


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db),
    http_request: Request = None
):
    """
    Create a new session for bot detection tracking.
    
    Args:
        request: Session creation request data
        db: Database session
        http_request: HTTP request object
        
    Returns:
        Session creation response with session ID
    """
    try:
        # Generate session ID
        session_id = generate_session_id()
        
        # Extract client information
        user_agent = sanitize_user_agent(request.user_agent or http_request.headers.get("user-agent", ""))
        ip_address = extract_ip_from_headers(dict(http_request.headers)) if http_request else None
        referrer = request.referrer or http_request.headers.get("referer", "") if http_request else ""
        
        # Create session record
        session = SessionModel(
            id=session_id,
            user_agent=user_agent,
            ip_address=ip_address,
            referrer=referrer,
            is_active=True
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"Created new session: {session_id}")
        
        return CreateSessionResponse(
            session_id=session_id,
            message="Session created successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.post("/sessions/{session_id}/data", response_model=IngestDataResponse)
async def ingest_data(
    session_id: str,
    request: IngestDataRequest,
    db: Session = Depends(get_db)
):
    """
    Ingest behavior data for a session and perform bot detection analysis.
    
    Args:
        session_id: Session ID
        request: Data ingestion request
        db: Database session
        
    Returns:
        Data ingestion response with analysis results
    """
    start_time = get_current_timestamp()
    
    try:
        # Validate session exists
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not session.is_active:
            raise HTTPException(status_code=400, detail="Session is not active")
        
        # Validate and process events
        valid_events = []
        for event in request.events:
            if validate_event_data(event):
                valid_events.append(event)
            else:
                logger.warning(f"Invalid event data received: {event}")
        
        if not valid_events:
            raise HTTPException(status_code=400, detail="No valid events provided")
        
        # Store behavior data
        behavior_records = []
        for event in valid_events:
            behavior_data = BehaviorData(
                id=generate_event_id(),
                session_id=session_id,
                event_type=event["event_type"],
                event_data=event.get("event_data", {}),
                page_url=event.get("page_url"),
                element_id=event.get("element_id"),
                element_type=event.get("element_type")
            )
            behavior_records.append(behavior_data)
        
        db.add_all(behavior_records)
        
        # Update session activity
        session.update_activity()
        
        # Perform bot detection analysis
        bot_score, confidence, is_bot, analysis_details = detection_engine.analyze_session(valid_events)
        
        # Store detection result
        detection_result = DetectionResult.create_result(
            session_id=session_id,
            bot_score=bot_score,
            confidence=confidence,
            is_bot=is_bot,
            processing_time_ms=calculate_processing_time(start_time),
            event_count=len(valid_events),
            analysis_details=analysis_details
        )
        
        db.add(detection_result)
        
        # Update session with final classification if confidence is high enough
        if confidence >= 0.7:
            session.is_bot = is_bot
        
        db.commit()
        
        logger.info(f"Processed {len(valid_events)} events for session {session_id}")
        
        return IngestDataResponse(
            session_id=session_id,
            events_processed=len(valid_events),
            bot_score=bot_score,
            confidence=confidence,
            is_bot=is_bot,
            processing_time_ms=calculate_processing_time(start_time)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to ingest data for session {session_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to process data")


@router.get("/sessions/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the current status and latest detection results for a session.
    
    Args:
        session_id: Session ID
        db: Database session
        
    Returns:
        Session status response
    """
    try:
        # Get session
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get event count
        event_count = db.query(BehaviorData).filter(BehaviorData.session_id == session_id).count()
        
        # Get latest detection result
        latest_result = db.query(DetectionResult).filter(
            DetectionResult.session_id == session_id
        ).order_by(DetectionResult.created_at.desc()).first()
        
        latest_result_dict = None
        if latest_result:
            latest_result_dict = latest_result.to_dict()
        
        return SessionStatusResponse(
            session_id=session_id,
            is_active=session.is_active,
            is_bot=session.is_bot,
            event_count=event_count,
            last_activity=session.last_activity.isoformat() if session.last_activity else None,
            latest_result=latest_result_dict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session status for {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session status")


@router.get("/sessions/{session_id}/events")
async def get_session_events(
    session_id: str,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get behavior events for a session.
    
    Args:
        session_id: Session ID
        limit: Maximum number of events to return
        offset: Number of events to skip
        db: Database session
        
    Returns:
        List of behavior events
    """
    try:
        # Validate session exists
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get events
        events = db.query(BehaviorData).filter(
            BehaviorData.session_id == session_id
        ).order_by(BehaviorData.timestamp.desc()).offset(offset).limit(limit).all()
        
        return format_success_response(
            data=[event.to_dict() for event in events],
            message=f"Retrieved {len(events)} events"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get events for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get events")


@router.get("/sessions/{session_id}/results")
async def get_session_results(
    session_id: str,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get detection results for a session.
    
    Args:
        session_id: Session ID
        limit: Maximum number of results to return
        offset: Number of results to skip
        db: Database session
        
    Returns:
        List of detection results
    """
    try:
        # Validate session exists
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get results
        results = db.query(DetectionResult).filter(
            DetectionResult.session_id == session_id
        ).order_by(DetectionResult.created_at.desc()).offset(offset).limit(limit).all()
        
        return format_success_response(
            data=[result.to_dict() for result in results],
            message=f"Retrieved {len(results)} results"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get results for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get results") 