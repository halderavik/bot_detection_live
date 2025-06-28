"""
Integration controller for survey platform integrations.

This module handles HTTP requests related to survey platform integrations
including Qualtrics and Decipher data processing and bot detection.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.database import get_db
from models.session import Session as SessionModel
from models.behavior_data import BehaviorData
from models.detection_result import DetectionResult
from services.integrations.qualtrics_integration import QualtricsIntegration
from services.integrations.decipher_integration import DecipherIntegration
from services.bot_detection_engine import BotDetectionEngine
from utils.logger import get_logger
from utils.helpers import format_success_response, generate_session_id

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/integrations", tags=["integrations"])

# Initialize integrations
qualtrics_integration = QualtricsIntegration()
decipher_integration = DecipherIntegration()
detection_engine = BotDetectionEngine()


# Pydantic models for request/response validation
class SurveyAnalysisRequest(BaseModel):
    """Request model for survey analysis."""
    survey_id: str
    platform: str  # "qualtrics" or "decipher"
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class SurveyAnalysisResponse(BaseModel):
    """Response model for survey analysis."""
    survey_id: str
    platform: str
    total_responses: int
    analyzed_responses: int
    bot_detections: int
    processing_time_ms: float


class IntegrationStatusResponse(BaseModel):
    """Response model for integration status."""
    platform: str
    configured: bool
    status: str


@router.get("/status")
async def get_integration_status():
    """
    Get status of all integrations.
    
    Returns:
        Integration status for all platforms
    """
    try:
        statuses = []
        
        # Qualtrics status
        qualtrics_status = IntegrationStatusResponse(
            platform="qualtrics",
            configured=qualtrics_integration.is_configured(),
            status="active" if qualtrics_integration.is_configured() else "not_configured"
        )
        statuses.append(qualtrics_status)
        
        # Decipher status
        decipher_status = IntegrationStatusResponse(
            platform="decipher",
            configured=decipher_integration.is_configured(),
            status="active" if decipher_integration.is_configured() else "not_configured"
        )
        statuses.append(decipher_status)
        
        return format_success_response(
            data=statuses,
            message="Integration status retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get integration status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get integration status")


@router.post("/qualtrics/analyze", response_model=SurveyAnalysisResponse)
async def analyze_qualtrics_survey(
    request: SurveyAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze Qualtrics survey responses for bot detection.
    
    Args:
        request: Survey analysis request
        db: Database session
        
    Returns:
        Survey analysis results
    """
    if not qualtrics_integration.is_configured():
        raise HTTPException(status_code=400, detail="Qualtrics integration not configured")
    
    try:
        # Get survey responses
        responses = qualtrics_integration.get_survey_responses(
            request.survey_id,
            request.start_date,
            request.end_date
        )
        
        if not responses:
            return SurveyAnalysisResponse(
                survey_id=request.survey_id,
                platform="qualtrics",
                total_responses=0,
                analyzed_responses=0,
                bot_detections=0,
                processing_time_ms=0.0
            )
        
        analyzed_count = 0
        bot_detections = 0
        
        # Process each response
        for response in responses:
            try:
                # Extract behavior data
                events = qualtrics_integration.extract_behavior_data(response)
                
                if not events:
                    continue
                
                # Create session for this response
                session_id = generate_session_id()
                session = SessionModel(
                    id=session_id,
                    user_agent=response.get("userAgent", ""),
                    ip_address=response.get("ipAddress"),
                    referrer=response.get("referer", ""),
                    is_active=False  # Survey responses are completed
                )
                db.add(session)
                
                # Store behavior data
                behavior_records = []
                for event in events:
                    behavior_data = BehaviorData(
                        id=event.get("id", generate_session_id()),
                        session_id=session_id,
                        event_type=event["event_type"],
                        event_data=event.get("event_data", {}),
                        page_url=event.get("page_url"),
                        element_id=event.get("element_id"),
                        element_type=event.get("element_type")
                    )
                    behavior_records.append(behavior_data)
                
                db.add_all(behavior_records)
                
                # Perform bot detection
                bot_score, confidence, is_bot, analysis_details = detection_engine.analyze_session(events)
                
                # Store detection result
                detection_result = DetectionResult.create_result(
                    session_id=session_id,
                    bot_score=bot_score,
                    confidence=confidence,
                    is_bot=is_bot,
                    processing_time_ms=0.0,  # Will be calculated below
                    event_count=len(events),
                    analysis_details=analysis_details
                )
                db.add(detection_result)
                
                # Update session with classification
                if confidence >= 0.7:
                    session.is_bot = is_bot
                
                # Flag response in Qualtrics if bot detected
                if is_bot and confidence >= 0.7:
                    qualtrics_integration.flag_response_as_bot(
                        request.survey_id,
                        response.get("responseId"),
                        bot_score,
                        analysis_details
                    )
                    bot_detections += 1
                
                analyzed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to analyze response {response.get('responseId')}: {e}")
                continue
        
        db.commit()
        
        return SurveyAnalysisResponse(
            survey_id=request.survey_id,
            platform="qualtrics",
            total_responses=len(responses),
            analyzed_responses=analyzed_count,
            bot_detections=bot_detections,
            processing_time_ms=0.0  # TODO: Calculate actual processing time
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze Qualtrics survey: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to analyze survey")


@router.post("/decipher/analyze", response_model=SurveyAnalysisResponse)
async def analyze_decipher_survey(
    request: SurveyAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze Decipher survey responses for bot detection.
    
    Args:
        request: Survey analysis request
        db: Database session
        
    Returns:
        Survey analysis results
    """
    if not decipher_integration.is_configured():
        raise HTTPException(status_code=400, detail="Decipher integration not configured")
    
    try:
        # Get survey responses
        responses = decipher_integration.get_survey_responses(
            request.survey_id,
            request.start_date,
            request.end_date
        )
        
        if not responses:
            return SurveyAnalysisResponse(
                survey_id=request.survey_id,
                platform="decipher",
                total_responses=0,
                analyzed_responses=0,
                bot_detections=0,
                processing_time_ms=0.0
            )
        
        analyzed_count = 0
        bot_detections = 0
        
        # Process each response
        for response in responses:
            try:
                # Extract behavior data
                events = decipher_integration.extract_behavior_data(response)
                
                if not events:
                    continue
                
                # Create session for this response
                session_id = generate_session_id()
                session = SessionModel(
                    id=session_id,
                    user_agent=response.get("userAgent", ""),
                    ip_address=response.get("ipAddress"),
                    referrer=response.get("referer", ""),
                    is_active=False  # Survey responses are completed
                )
                db.add(session)
                
                # Store behavior data
                behavior_records = []
                for event in events:
                    behavior_data = BehaviorData(
                        id=event.get("id", generate_session_id()),
                        session_id=session_id,
                        event_type=event["event_type"],
                        event_data=event.get("event_data", {}),
                        page_url=event.get("page_url"),
                        element_id=event.get("element_id"),
                        element_type=event.get("element_type")
                    )
                    behavior_records.append(behavior_data)
                
                db.add_all(behavior_records)
                
                # Perform bot detection
                bot_score, confidence, is_bot, analysis_details = detection_engine.analyze_session(events)
                
                # Store detection result
                detection_result = DetectionResult.create_result(
                    session_id=session_id,
                    bot_score=bot_score,
                    confidence=confidence,
                    is_bot=is_bot,
                    processing_time_ms=0.0,  # Will be calculated below
                    event_count=len(events),
                    analysis_details=analysis_details
                )
                db.add(detection_result)
                
                # Update session with classification
                if confidence >= 0.7:
                    session.is_bot = is_bot
                
                # Flag response in Decipher if bot detected
                if is_bot and confidence >= 0.7:
                    decipher_integration.flag_response_as_bot(
                        request.survey_id,
                        response.get("responseId"),
                        bot_score,
                        analysis_details
                    )
                    bot_detections += 1
                
                analyzed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to analyze response {response.get('responseId')}: {e}")
                continue
        
        db.commit()
        
        return SurveyAnalysisResponse(
            survey_id=request.survey_id,
            platform="decipher",
            total_responses=len(responses),
            analyzed_responses=analyzed_count,
            bot_detections=bot_detections,
            processing_time_ms=0.0  # TODO: Calculate actual processing time
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze Decipher survey: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to analyze survey")


@router.get("/qualtrics/surveys")
async def get_qualtrics_surveys():
    """
    Get list of available Qualtrics surveys.
    
    Returns:
        List of surveys
    """
    if not qualtrics_integration.is_configured():
        raise HTTPException(status_code=400, detail="Qualtrics integration not configured")
    
    try:
        # This would require additional API calls to get survey list
        # For now, return a placeholder
        return format_success_response(
            data=[],
            message="Survey list functionality not implemented yet"
        )
        
    except Exception as e:
        logger.error(f"Failed to get Qualtrics surveys: {e}")
        raise HTTPException(status_code=500, detail="Failed to get surveys")


@router.get("/decipher/surveys")
async def get_decipher_surveys():
    """
    Get list of available Decipher surveys.
    
    Returns:
        List of surveys
    """
    if not decipher_integration.is_configured():
        raise HTTPException(status_code=400, detail="Decipher integration not configured")
    
    try:
        # This would require additional API calls to get survey list
        # For now, return a placeholder
        return format_success_response(
            data=[],
            message="Survey list functionality not implemented yet"
        )
        
    except Exception as e:
        logger.error(f"Failed to get Decipher surveys: {e}")
        raise HTTPException(status_code=500, detail="Failed to get surveys")


@router.get("/qualtrics/survey/{survey_id}/metadata")
async def get_qualtrics_survey_metadata(survey_id: str):
    """
    Get metadata for a specific Qualtrics survey.
    
    Args:
        survey_id: Qualtrics survey ID
        
    Returns:
        Survey metadata
    """
    if not qualtrics_integration.is_configured():
        raise HTTPException(status_code=400, detail="Qualtrics integration not configured")
    
    try:
        metadata = qualtrics_integration.get_survey_metadata(survey_id)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        return format_success_response(
            data=metadata,
            message="Survey metadata retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Qualtrics survey metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to get survey metadata")


@router.get("/decipher/survey/{survey_id}/metadata")
async def get_decipher_survey_metadata(survey_id: str):
    """
    Get metadata for a specific Decipher survey.
    
    Args:
        survey_id: Decipher survey ID
        
    Returns:
        Survey metadata
    """
    if not decipher_integration.is_configured():
        raise HTTPException(status_code=400, detail="Decipher integration not configured")
    
    try:
        metadata = decipher_integration.get_survey_metadata(survey_id)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="Survey not found")
        
        return format_success_response(
            data=metadata,
            message="Survey metadata retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Decipher survey metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to get survey metadata")


@router.post("/qualtrics/survey/{survey_id}/export")
async def export_qualtrics_responses(
    survey_id: str,
    format: str = Query("json", description="Export format (json, csv, xlsx)"),
    start_date: Optional[str] = Query(None, description="Start date filter"),
    end_date: Optional[str] = Query(None, description="End date filter")
):
    """
    Export Qualtrics survey responses.
    
    Args:
        survey_id: Qualtrics survey ID
        format: Export format
        start_date: Start date filter
        end_date: End date filter
        
    Returns:
        Export URL
    """
    if not qualtrics_integration.is_configured():
        raise HTTPException(status_code=400, detail="Qualtrics integration not configured")
    
    try:
        # This would require additional API calls for export functionality
        # For now, return a placeholder
        return format_success_response(
            data={"export_url": None},
            message="Export functionality not implemented yet"
        )
        
    except Exception as e:
        logger.error(f"Failed to export Qualtrics responses: {e}")
        raise HTTPException(status_code=500, detail="Failed to export responses")


@router.post("/decipher/survey/{survey_id}/export")
async def export_decipher_responses(
    survey_id: str,
    format: str = Query("json", description="Export format (json, csv, xlsx)"),
    start_date: Optional[str] = Query(None, description="Start date filter"),
    end_date: Optional[str] = Query(None, description="End date filter")
):
    """
    Export Decipher survey responses.
    
    Args:
        survey_id: Decipher survey ID
        format: Export format
        start_date: Start date filter
        end_date: End date filter
        
    Returns:
        Export URL
    """
    if not decipher_integration.is_configured():
        raise HTTPException(status_code=400, detail="Decipher integration not configured")
    
    try:
        export_url = decipher_integration.export_responses(
            survey_id, format, start_date, end_date
        )
        
        return format_success_response(
            data={"export_url": export_url},
            message="Export initiated successfully" if export_url else "Export failed"
        )
        
    except Exception as e:
        logger.error(f"Failed to export Decipher responses: {e}")
        raise HTTPException(status_code=500, detail="Failed to export responses") 