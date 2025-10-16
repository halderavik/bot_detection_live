"""
Text Analysis API Controller.

This controller provides endpoints for submitting survey questions,
analyzing responses in real-time, and retrieving session summaries
with text quality analysis results.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from app.database import get_db
from app.models import Session, SurveyQuestion, SurveyResponse
from app.services.text_analysis_service import text_analysis_service, TextAnalysisResult
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/text-analysis", tags=["text-analysis"])

# Pydantic models for API requests and responses

class SubmitQuestionRequest(BaseModel):
    """Request model for submitting a survey question."""
    session_id: str = Field(..., description="Session ID")
    question_text: str = Field(..., description="Question text")
    question_type: Optional[str] = Field(None, description="Type of question (e.g., 'open_ended')")
    element_id: Optional[str] = Field(None, description="HTML element ID")
    element_type: Optional[str] = Field(None, description="HTML element type")
    page_url: Optional[str] = Field(None, description="Page URL where question appears")
    page_title: Optional[str] = Field(None, description="Page title")

class SubmitQuestionResponse(BaseModel):
    """Response model for question submission."""
    question_id: str
    session_id: str
    created_at: datetime

class SubmitResponseRequest(BaseModel):
    """Request model for submitting a survey response."""
    session_id: str = Field(..., description="Session ID")
    question_id: str = Field(..., description="Question ID")
    response_text: str = Field(..., description="Response text")
    response_time_ms: Optional[int] = Field(None, description="Time to respond in milliseconds")

class SubmitResponseResponse(BaseModel):
    """Response model for response submission with analysis."""
    response_id: str
    question_id: str
    session_id: str
    quality_score: Optional[float]
    is_flagged: bool
    flag_reasons: Dict[str, Any]
    analysis_details: Dict[str, Any]
    analyzed_at: datetime

class SessionSummaryResponse(BaseModel):
    """Response model for session text quality summary."""
    session_id: str
    total_responses: int
    avg_quality_score: Optional[float]
    flagged_count: int
    flagged_percentage: float
    responses: List[Dict[str, Any]]

class TextAnalysisStatsResponse(BaseModel):
    """Response model for OpenAI usage statistics."""
    total_requests: int
    total_tokens_input: int
    total_tokens_output: int
    estimated_cost: float
    errors: int
    cache_hits: int
    cache_hit_rate: float

# API Endpoints

@router.post("/questions", response_model=SubmitQuestionResponse)
async def submit_question(
    request: SubmitQuestionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a survey question for tracking.
    
    This endpoint stores question metadata that will be used later
    for text quality analysis when responses are submitted.
    """
    try:
        # Verify session exists
        session_result = await db.execute(
            select(Session).where(Session.id == request.session_id)
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {request.session_id} not found"
            )
        
        # Create survey question
        question = SurveyQuestion(
            id=str(uuid.uuid4()),
            session_id=request.session_id,
            question_text=request.question_text,
            question_type=request.question_type,
            element_id=request.element_id,
            element_type=request.element_type,
            page_url=request.page_url,
            page_title=request.page_title
        )
        
        db.add(question)
        await db.commit()
        await db.refresh(question)
        
        logger.info(f"Question submitted: {question.id} for session {request.session_id}")
        
        return SubmitQuestionResponse(
            question_id=question.id,
            session_id=question.session_id,
            created_at=question.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting question: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit question"
        )

@router.post("/responses", response_model=SubmitResponseResponse)
async def submit_response(
    request: SubmitResponseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a survey response and perform real-time text quality analysis.
    
    This endpoint analyzes the response using OpenAI GPT-4o-mini and returns
    quality scores, flag reasons, and detailed analysis results.
    """
    try:
        # Verify session and question exist
        session_result = await db.execute(
            select(Session).where(Session.id == request.session_id)
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {request.session_id} not found"
            )
        
        question_result = await db.execute(
            select(SurveyQuestion).where(SurveyQuestion.id == request.question_id)
        )
        question = question_result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question {request.question_id} not found"
            )
        
        # Perform text analysis
        analysis_result = await text_analysis_service.analyze_response(
            question.question_text,
            request.response_text
        )
        
        # Create survey response
        response = SurveyResponse(
            id=str(uuid.uuid4()),
            question_id=request.question_id,
            session_id=request.session_id,
            response_text=request.response_text,
            response_time_ms=request.response_time_ms,
            text_analysis_result=analysis_result.analysis_details,
            quality_score=analysis_result.quality_score,
            is_flagged=analysis_result.is_flagged,
            flag_reasons=analysis_result.flag_reasons,
            gibberish_score=analysis_result.gibberish_score,
            copy_paste_score=analysis_result.copy_paste_score,
            relevance_score=analysis_result.relevance_score,
            generic_score=analysis_result.generic_score,
            analyzed_at=datetime.utcnow()
        )
        
        db.add(response)
        await db.commit()
        await db.refresh(response)
        
        logger.info(f"Response analyzed: {response.id}, Quality: {analysis_result.quality_score}")
        
        return SubmitResponseResponse(
            response_id=response.id,
            question_id=response.question_id,
            session_id=response.session_id,
            quality_score=response.quality_score,
            is_flagged=response.is_flagged,
            flag_reasons=response.flag_reasons or {},
            analysis_details=response.text_analysis_result or {},
            analyzed_at=response.analyzed_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting response: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit response"
        )

@router.get("/sessions/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_session_summary(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get text quality summary for a session.
    
    Returns aggregated statistics about text quality analysis results
    for all responses in the session.
    """
    try:
        # Verify session exists
        session_result = await db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # Get all responses for the session
        responses_result = await db.execute(
            select(SurveyResponse).where(SurveyResponse.session_id == session_id)
        )
        responses = responses_result.scalars().all()
        
        # Calculate summary statistics
        total_responses = len(responses)
        flagged_count = sum(1 for r in responses if r.is_flagged)
        quality_scores = [r.quality_score for r in responses if r.quality_score is not None]
        
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else None
        flagged_percentage = (flagged_count / total_responses * 100) if total_responses > 0 else 0
        
        # Format response data
        response_data = []
        for response in responses:
            response_data.append({
                "response_id": response.id,
                "question_id": response.question_id,
                "quality_score": response.quality_score,
                "is_flagged": response.is_flagged,
                "flag_reasons": response.flag_reasons or {},
                "analyzed_at": response.analyzed_at,
                "truncated_text": response.truncated_response_text
            })
        
        logger.info(f"Session summary generated for {session_id}: {total_responses} responses")
        
        return SessionSummaryResponse(
            session_id=session_id,
            total_responses=total_responses,
            avg_quality_score=avg_quality_score,
            flagged_count=flagged_count,
            flagged_percentage=flagged_percentage,
            responses=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session summary"
        )

@router.get("/health")
async def text_analysis_health():
    """
    Check text analysis service health and configuration.
    
    Returns OpenAI service availability and configuration status without exposing secrets.
    """
    try:
        openai_service = text_analysis_service.openai_service
        
        return {
            "status": "healthy",
            "openai_available": openai_service.is_available,
            "model": openai_service.model if openai_service.is_available else None,
            "max_tokens": openai_service.max_tokens if openai_service.is_available else None,
            "temperature": openai_service.temperature if openai_service.is_available else None,
            "rate_limiter_enabled": True,
            "cache_enabled": True,
            "service_initialized": True
        }
        
    except Exception as e:
        logger.error(f"Error checking text analysis health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check text analysis health"
        )

@router.get("/stats", response_model=TextAnalysisStatsResponse)
async def get_text_analysis_stats():
    """
    Get OpenAI API usage statistics and performance metrics.
    
    Returns information about API calls, token usage, costs, and caching.
    """
    try:
        stats = text_analysis_service.openai_service.get_usage_stats()
        
        return TextAnalysisStatsResponse(
            total_requests=stats["total_requests"],
            total_tokens_input=stats["total_tokens_input"],
            total_tokens_output=stats["total_tokens_output"],
            estimated_cost=stats["estimated_cost"],
            errors=stats["errors"],
            cache_hits=stats["cache_hits"],
            cache_hit_rate=stats["cache_hit_rate"]
        )
        
    except Exception as e:
        logger.error(f"Error getting text analysis stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get text analysis statistics"
        )

@router.post("/batch-analyze")
async def batch_analyze_responses(
    questions_and_answers: List[Dict[str, str]],
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze multiple question-answer pairs in batch.
    
    This endpoint is useful for analyzing historical data or bulk processing.
    """
    try:
        if not questions_and_answers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No questions and answers provided"
            )
        
        # Extract questions and answers
        qa_pairs = [(item["question"], item["answer"]) for item in questions_and_answers]
        
        # Perform batch analysis
        results = await text_analysis_service.batch_analyze_responses(qa_pairs)
        
        # Get summary statistics
        summary = text_analysis_service.get_analysis_summary(results)
        
        # Format results
        formatted_results = []
        for i, result in enumerate(results):
            formatted_results.append({
                "index": i,
                "quality_score": result.quality_score,
                "is_flagged": result.is_flagged,
                "flag_reasons": result.flag_reasons,
                "analysis_details": result.analysis_details,
                "confidence": result.confidence
            })
        
        logger.info(f"Batch analysis completed: {len(results)} responses analyzed")
        
        return {
            "summary": summary,
            "results": formatted_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform batch analysis"
        )

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    days: int = 7,
    survey_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get aggregated text quality statistics for dashboard.
    
    Returns overall quality metrics across all sessions or filtered by survey.
    """
    try:
        # Calculate date range
        from datetime import timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Build query conditions
        conditions = [
            SurveyResponse.analyzed_at >= start_date,
            SurveyResponse.analyzed_at <= end_date
        ]
        
        if survey_id:
            # Join with Session table to filter by survey_id
            query = (
                select(SurveyResponse)
                .join(Session, SurveyResponse.session_id == Session.id)
                .where(
                    and_(
                        *conditions,
                        Session.survey_id == survey_id
                    )
                )
            )
        else:
            query = select(SurveyResponse).where(and_(*conditions))
        
        result = await db.execute(query)
        responses = result.scalars().all()
        
        if not responses:
            return {
                "total_responses": 0,
                "avg_quality_score": None,
                "flagged_count": 0,
                "flagged_percentage": 0.0,
                "quality_distribution": {},
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": days
                }
            }
        
        # Calculate statistics
        total_responses = len(responses)
        quality_scores = [r.quality_score for r in responses if r.quality_score is not None]
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else None
        flagged_count = sum(1 for r in responses if r.is_flagged)
        flagged_percentage = (flagged_count / total_responses * 100) if total_responses > 0 else 0
        
        # Calculate quality distribution (0-10, 10-20, ..., 90-100)
        quality_distribution = {}
        for i in range(10):
            bucket_start = i * 10
            bucket_end = (i + 1) * 10
            count = sum(1 for score in quality_scores if bucket_start <= score < bucket_end)
            quality_distribution[f"{bucket_start}-{bucket_end}"] = count
        
        logger.info(f"Dashboard summary generated: {total_responses} responses, {flagged_count} flagged")
        
        return {
            "total_responses": total_responses,
            "avg_quality_score": avg_quality_score,
            "flagged_count": flagged_count,
            "flagged_percentage": flagged_percentage,
            "quality_distribution": quality_distribution,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard summary"
        )

@router.get("/dashboard/respondents")
async def get_respondent_analysis(
    survey_id: Optional[str] = None,
    days: int = 30,
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get respondent-level text analysis data with all findings and reasons.
    
    Returns paginated list of respondents with their text quality metrics.
    """
    try:
        # Calculate date range
        from datetime import timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Build query to get sessions with their text analysis data
        base_query = (
            select(Session, func.count(SurveyResponse.id).label('response_count'))
            .outerjoin(SurveyResponse, Session.id == SurveyResponse.session_id)
            .where(
                and_(
                    Session.created_at >= start_date,
                    Session.created_at <= end_date
                )
            )
        )
        
        if survey_id:
            base_query = base_query.where(Session.survey_id == survey_id)
        
        base_query = base_query.group_by(Session.id)
        
        # Add pagination
        offset = (page - 1) * limit
        query = base_query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        sessions_with_counts = result.all()
        
        # Get detailed response data for these sessions
        respondents = []
        for session, response_count in sessions_with_counts:
            if response_count == 0:
                # Session has no text responses
                respondents.append({
                    "respondent_id": session.respondent_id,
                    "session_id": session.id,
                    "survey_id": session.survey_id,
                    "response_count": 0,
                    "avg_quality_score": None,
                    "flagged_count": 0,
                    "flagged_percentage": 0.0,
                    "quality_scores": [],
                    "flag_reasons_summary": {},
                    "analyzed_at": None
                })
            else:
                # Get responses for this session
                responses_query = (
                    select(SurveyResponse)
                    .where(SurveyResponse.session_id == session.id)
                )
                responses_result = await db.execute(responses_query)
                session_responses = responses_result.scalars().all()
                
                # Calculate metrics
                quality_scores = [r.quality_score for r in session_responses if r.quality_score is not None]
                avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else None
                flagged_count = sum(1 for r in session_responses if r.is_flagged)
                flagged_percentage = (flagged_count / len(session_responses) * 100) if session_responses else 0
                
                # Aggregate flag reasons
                flag_reasons_summary = {}
                for response in session_responses:
                    if response.flag_reasons:
                        for flag_type, flag_data in response.flag_reasons.items():
                            if flag_type not in flag_reasons_summary:
                                flag_reasons_summary[flag_type] = 0
                            flag_reasons_summary[flag_type] += 1
                
                # Get latest analysis date
                analyzed_at = max([r.analyzed_at for r in session_responses if r.analyzed_at], default=None)
                
                respondents.append({
                    "respondent_id": session.respondent_id,
                    "session_id": session.id,
                    "survey_id": session.survey_id,
                    "response_count": len(session_responses),
                    "avg_quality_score": avg_quality_score,
                    "flagged_count": flagged_count,
                    "flagged_percentage": flagged_percentage,
                    "quality_scores": quality_scores,
                    "flag_reasons_summary": flag_reasons_summary,
                    "analyzed_at": analyzed_at.isoformat() if analyzed_at else None
                })
        
        # Get total count for pagination
        count_query = select(func.count(Session.id)).where(
            and_(
                Session.created_at >= start_date,
                Session.created_at <= end_date
            )
        )
        if survey_id:
            count_query = count_query.where(Session.survey_id == survey_id)
        
        count_result = await db.execute(count_query)
        total_count = count_result.scalar()
        
        logger.info(f"Respondent analysis generated: {len(respondents)} respondents, page {page}")
        
        return {
            "respondents": respondents,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            },
            "filters": {
                "survey_id": survey_id,
                "days": days,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting respondent analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get respondent analysis"
        )