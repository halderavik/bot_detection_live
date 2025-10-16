"""
Report generation service.

This service handles the generation of survey reports including
summary statistics and detailed respondent data with CSV export functionality.
"""

import csv
import io
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
import logging

from app.models import Session, BehaviorData, DetectionResult, SurveyResponse
from app.models.report_models import (
    SurveySummaryReport, DetailedReport, RespondentDetail,
    ReportRequest, ReportResponse, ReportType, ReportFormat
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ReportService:
    """Service for generating survey reports."""
    
    def __init__(self):
        """Initialize the report service."""
        self.logger = logger
    
    async def get_available_surveys(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Get list of available surveys with basic statistics.
        
        Args:
            db: Database session
            
        Returns:
            List of survey information with statistics
        """
        try:
            # Get unique survey IDs with basic stats
            query = (
                select(
                    Session.survey_id,
                    Session.platform,
                    func.count(Session.id).label('session_count'),
                    func.min(Session.created_at).label('first_session'),
                    func.max(Session.created_at).label('last_session')
                )
                .where(Session.survey_id.isnot(None))
                .group_by(Session.survey_id, Session.platform)
                .order_by(func.count(Session.id).desc())
            )
            
            result = await db.execute(query)
            surveys = []
            
            for row in result:
                # Get bot detection count for this survey
                bot_count_query = (
                    select(func.count(DetectionResult.id))
                    .join(Session, DetectionResult.session_id == Session.id)
                    .where(
                        and_(
                            Session.survey_id == row.survey_id,
                            DetectionResult.is_bot == True
                        )
                    )
                )
                bot_result = await db.execute(bot_count_query)
                bot_count = bot_result.scalar() or 0
                
                surveys.append({
                    "survey_id": row.survey_id,
                    "platform": row.platform,
                    "session_count": row.session_count,
                    "bot_count": bot_count,
                    "human_count": row.session_count - bot_count,
                    "bot_rate": (bot_count / row.session_count * 100) if row.session_count > 0 else 0,
                    "first_session": row.first_session.isoformat() if row.first_session else None,
                    "last_session": row.last_session.isoformat() if row.last_session else None
                })
            
            return surveys
            
        except Exception as e:
            self.logger.error(f"Error getting available surveys: {e}")
            raise
    
    async def generate_summary_report(
        self, 
        survey_id: str, 
        db: AsyncSession,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        include_inactive: bool = False
    ) -> SurveySummaryReport:
        """
        Generate a summary report for a specific survey.
        
        Args:
            survey_id: Survey identifier
            db: Database session
            date_from: Start date filter
            date_to: End date filter
            include_inactive: Whether to include inactive sessions
            
        Returns:
            Survey summary report
        """
        try:
            # Build base query for sessions
            base_conditions = [Session.survey_id == survey_id]
            
            if not include_inactive:
                base_conditions.append(Session.is_active == True)
            
            if date_from:
                base_conditions.append(Session.created_at >= date_from)
            
            if date_to:
                base_conditions.append(Session.created_at <= date_to)
            
            # Get session statistics
            session_query = select(Session).where(and_(*base_conditions))
            session_result = await db.execute(session_query)
            sessions = session_result.scalars().all()
            
            total_sessions = len(sessions)
            if total_sessions == 0:
                return SurveySummaryReport(
                    survey_id=survey_id,
                    total_respondents=0,
                    total_sessions=0,
                    bot_detections=0,
                    human_respondents=0,
                    bot_detection_rate=0.0,
                    activity_distribution={},
                    risk_distribution={},
                    date_range={
                        "from": date_from.isoformat() if date_from else None,
                        "to": date_to.isoformat() if date_to else None
                    }
                )
            
            # Get detection results for these sessions
            session_ids = [session.id for session in sessions]
            detection_query = (
                select(DetectionResult)
                .where(DetectionResult.session_id.in_(session_ids))
                .order_by(DetectionResult.created_at.desc())
            )
            detection_result = await db.execute(detection_query)
            detections = detection_result.scalars().all()
            
            # Get latest detection for each session
            latest_detections = {}
            for detection in detections:
                if detection.session_id not in latest_detections:
                    latest_detections[detection.session_id] = detection
            
            # Calculate statistics
            bot_detections = sum(1 for det in latest_detections.values() if det.is_bot)
            human_respondents = total_sessions - bot_detections
            bot_detection_rate = (bot_detections / total_sessions * 100) if total_sessions > 0 else 0
            
            # Get activity distribution
            activity_query = (
                select(BehaviorData.event_type, func.count(BehaviorData.id))
                .join(Session, BehaviorData.session_id == Session.id)
                .where(and_(*base_conditions))
                .group_by(BehaviorData.event_type)
            )
            activity_result = await db.execute(activity_query)
            activity_distribution = dict(activity_result.all())
            
            # Get risk level distribution
            risk_distribution = {}
            for detection in latest_detections.values():
                risk_level = detection.risk_level
                risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
            
            # Calculate average session duration
            total_duration = 0
            sessions_with_duration = 0
            total_events = 0
            
            for session in sessions:
                if session.last_activity and session.created_at:
                    duration = (session.last_activity - session.created_at).total_seconds() / 60
                    total_duration += duration
                    sessions_with_duration += 1
                
                # Get event count for this session
                event_count_query = select(func.count(BehaviorData.id)).where(
                    BehaviorData.session_id == session.id
                )
                event_result = await db.execute(event_count_query)
                event_count = event_result.scalar() or 0
                total_events += event_count
            
            average_session_duration = (
                total_duration / sessions_with_duration 
                if sessions_with_duration > 0 else None
            )
            average_events_per_session = (
                total_events / total_sessions 
                if total_sessions > 0 else None
            )
            
            # Get platform information
            platform = sessions[0].platform if sessions else None
            
            # Get date range
            if sessions:
                min_date = min(session.created_at for session in sessions)
                max_date = max(session.created_at for session in sessions)
                date_range = {
                    "from": min_date.isoformat(),
                    "to": max_date.isoformat()
                }
            else:
                date_range = {
                    "from": date_from.isoformat() if date_from else None,
                    "to": date_to.isoformat() if date_to else None
                }
            
            # Get text quality analysis data
            text_quality_summary = None
            if sessions:
                session_ids = [session.id for session in sessions]
                
                # Get text responses for these sessions
                text_responses_query = select(SurveyResponse).where(
                    SurveyResponse.session_id.in_(session_ids)
                )
                text_responses_result = await db.execute(text_responses_query)
                text_responses = text_responses_result.scalars().all()
                
                if text_responses:
                    total_text_responses = len(text_responses)
                    quality_scores = [r.quality_score for r in text_responses if r.quality_score is not None]
                    avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else None
                    flagged_count = sum(1 for r in text_responses if r.is_flagged)
                    flagged_percentage = (flagged_count / total_text_responses * 100) if total_text_responses > 0 else 0
                    
                    # Calculate quality distribution
                    quality_distribution = {}
                    for i in range(10):
                        bucket_start = i * 10
                        bucket_end = (i + 1) * 10
                        count = sum(1 for score in quality_scores if bucket_start <= score < bucket_end)
                        quality_distribution[f"{bucket_start}-{bucket_end}"] = count
                    
                    text_quality_summary = {
                        "total_responses": total_text_responses,
                        "avg_quality_score": avg_quality_score,
                        "flagged_count": flagged_count,
                        "flagged_percentage": flagged_percentage,
                        "quality_distribution": quality_distribution
                    }
            
            return SurveySummaryReport(
                survey_id=survey_id,
                total_respondents=total_sessions,
                total_sessions=total_sessions,
                bot_detections=bot_detections,
                human_respondents=human_respondents,
                bot_detection_rate=bot_detection_rate,
                activity_distribution=activity_distribution,
                risk_distribution=risk_distribution,
                platform=platform,
                date_range=date_range,
                average_session_duration=average_session_duration,
                average_events_per_session=average_events_per_session,
                text_quality_summary=text_quality_summary
            )
            
        except Exception as e:
            self.logger.error(f"Error generating summary report: {e}")
            raise
    
    async def generate_detailed_report(
        self, 
        survey_id: str, 
        db: AsyncSession,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        include_inactive: bool = False
    ) -> DetailedReport:
        """
        Generate a detailed report for a specific survey.
        
        Args:
            survey_id: Survey identifier
            db: Database session
            date_from: Start date filter
            date_to: End date filter
            include_inactive: Whether to include inactive sessions
            
        Returns:
            Detailed report with all respondents
        """
        try:
            # Build base query for sessions
            base_conditions = [Session.survey_id == survey_id]
            
            if not include_inactive:
                base_conditions.append(Session.is_active == True)
            
            if date_from:
                base_conditions.append(Session.created_at >= date_from)
            
            if date_to:
                base_conditions.append(Session.created_at <= date_to)
            
            # Get sessions with all related data
            session_query = (
                select(Session)
                .options(
                    selectinload(Session.behavior_data),
                    selectinload(Session.detection_results)
                )
                .where(and_(*base_conditions))
                .order_by(Session.created_at.desc())
            )
            
            session_result = await db.execute(session_query)
            sessions = session_result.scalars().all()
            
            # Generate summary statistics
            summary_stats = await self._generate_summary_stats(sessions)
            
            # Generate respondent details
            respondents = []
            for session in sessions:
                respondent_detail = await self._create_respondent_detail(session)
                respondents.append(respondent_detail)
            
            return DetailedReport(
                survey_id=survey_id,
                total_respondents=len(sessions),
                generated_at=datetime.utcnow(),
                summary_stats=summary_stats,
                respondents=respondents
            )
            
        except Exception as e:
            self.logger.error(f"Error generating detailed report: {e}")
            raise
    
    async def _generate_summary_stats(self, sessions: List[Session]) -> Dict[str, Any]:
        """Generate summary statistics from sessions."""
        if not sessions:
            return {}
        
        total_sessions = len(sessions)
        bot_count = 0
        risk_distribution = {}
        activity_distribution = {}
        
        for session in sessions:
            # Get latest detection result
            latest_detection = None
            if session.detection_results:
                latest_detection = max(session.detection_results, key=lambda x: x.created_at)
                if latest_detection.is_bot:
                    bot_count += 1
                
                # Risk distribution
                risk_level = latest_detection.risk_level
                risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
            
            # Activity distribution
            for event in session.behavior_data:
                event_type = event.event_type
                activity_distribution[event_type] = activity_distribution.get(event_type, 0) + 1
        
        return {
            "total_sessions": total_sessions,
            "bot_detections": bot_count,
            "human_respondents": total_sessions - bot_count,
            "bot_detection_rate": (bot_count / total_sessions * 100) if total_sessions > 0 else 0,
            "risk_distribution": risk_distribution,
            "activity_distribution": activity_distribution
        }
    
    async def _create_respondent_detail(self, session: Session) -> RespondentDetail:
        """Create respondent detail from session data."""
        # Get latest detection result
        latest_detection = None
        if session.detection_results:
            latest_detection = max(session.detection_results, key=lambda x: x.created_at)
        
        # Calculate session duration
        session_duration = 0
        if session.last_activity and session.created_at:
            session_duration = (session.last_activity - session.created_at).total_seconds() / 60
        
        # Get event breakdown
        event_breakdown = {}
        for event in session.behavior_data:
            event_type = event.event_type
            event_breakdown[event_type] = event_breakdown.get(event_type, 0) + 1
        
        # Get method scores and analysis
        method_scores = {}
        analysis_summary = None
        flagged_patterns = None
        bot_explanation = None
        
        if latest_detection:
            method_scores = latest_detection.method_scores or {}
            analysis_summary = latest_detection.analysis_summary
            flagged_patterns = latest_detection.flagged_patterns
            
            if latest_detection.is_bot:
                bot_explanation = self._generate_bot_explanation(latest_detection)
        
        # Get text quality data for this session
        text_response_count = None
        avg_text_quality_score = None
        flagged_text_responses = None
        text_quality_percentage = None
        
        # This would need to be passed from the calling method or queried here
        # For now, we'll add the fields but they'll be None until we implement the query
        
        return RespondentDetail(
            session_id=session.id,
            respondent_id=session.respondent_id,
            created_at=session.created_at,
            last_activity=session.last_activity or session.created_at,
            is_bot=latest_detection.is_bot if latest_detection else False,
            confidence_score=latest_detection.confidence_score if latest_detection else 0.0,
            risk_level=latest_detection.risk_level if latest_detection else "unknown",
            total_events=len(session.behavior_data),
            session_duration_minutes=session_duration,
            event_breakdown=event_breakdown,
            method_scores=method_scores,
            flagged_patterns=flagged_patterns,
            analysis_summary=analysis_summary,
            bot_explanation=bot_explanation,
            text_response_count=text_response_count,
            avg_text_quality_score=avg_text_quality_score,
            flagged_text_responses=flagged_text_responses,
            text_quality_percentage=text_quality_percentage
        )
    
    def _generate_bot_explanation(self, detection: DetectionResult) -> str:
        """Generate human-readable bot explanation."""
        explanations = []
        
        if detection.flagged_patterns:
            for pattern_type, details in detection.flagged_patterns.items():
                if isinstance(details, dict):
                    count = details.get('count', 0)
                    severity = details.get('severity', 'unknown')
                    explanations.append(f"{pattern_type}: {count} suspicious events ({severity} severity)")
                else:
                    explanations.append(f"{pattern_type}: {details}")
        
        if detection.method_scores:
            high_score_methods = [
                method for method, score in detection.method_scores.items() 
                if score > 0.7
            ]
            if high_score_methods:
                explanations.append(f"High-risk methods: {', '.join(high_score_methods)}")
        
        if detection.analysis_summary:
            explanations.append(f"Analysis: {detection.analysis_summary}")
        
        return "; ".join(explanations) if explanations else "Bot behavior detected based on multiple indicators"
    
    def generate_csv_report(self, detailed_report: DetailedReport) -> str:
        """
        Generate CSV content from detailed report.
        
        Args:
            detailed_report: Detailed report data
            
        Returns:
            CSV content as string
        """
        try:
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            header = [
                "Session ID", "Respondent ID", "Created At", "Last Activity",
                "Is Bot", "Confidence Score", "Risk Level", "Total Events",
                "Session Duration (min)", "Event Breakdown", "Method Scores",
                "Flagged Patterns", "Analysis Summary", "Bot Explanation",
                "Text Response Count", "Avg Text Quality Score", "Flagged Text Responses", "Text Quality Percentage"
            ]
            writer.writerow(header)
            
            # Write data rows
            for respondent in detailed_report.respondents:
                row = [
                    respondent.session_id,
                    respondent.respondent_id or "",
                    respondent.created_at.isoformat(),
                    respondent.last_activity.isoformat(),
                    "Yes" if respondent.is_bot else "No",
                    f"{respondent.confidence_score:.3f}",
                    respondent.risk_level,
                    respondent.total_events,
                    f"{respondent.session_duration_minutes:.2f}",
                    json.dumps(respondent.event_breakdown),
                    json.dumps(respondent.method_scores),
                    json.dumps(respondent.flagged_patterns) if respondent.flagged_patterns else "",
                    respondent.analysis_summary or "",
                    respondent.bot_explanation or "",
                    respondent.text_response_count or 0,
                    f"{respondent.avg_text_quality_score:.1f}" if respondent.avg_text_quality_score else "N/A",
                    respondent.flagged_text_responses or 0,
                    f"{respondent.text_quality_percentage:.1f}%" if respondent.text_quality_percentage else "N/A"
                ]
                writer.writerow(row)
            
            return output.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error generating CSV report: {e}")
            raise
    
    async def generate_report(
        self, 
        request: ReportRequest, 
        db: AsyncSession
    ) -> ReportResponse:
        """
        Generate a report based on the request.
        
        Args:
            request: Report generation request
            db: Database session
            
        Returns:
            Report response with data or download URL
        """
        try:
            if request.report_type == ReportType.SUMMARY:
                summary_data = await self.generate_summary_report(
                    request.survey_id, 
                    db, 
                    request.date_from, 
                    request.date_to, 
                    request.include_inactive
                )
                
                return ReportResponse(
                    success=True,
                    report_type=request.report_type,
                    format=request.format,
                    generated_at=datetime.utcnow(),
                    summary_data=summary_data
                )
            
            elif request.report_type == ReportType.DETAILED:
                detailed_data = await self.generate_detailed_report(
                    request.survey_id, 
                    db, 
                    request.date_from, 
                    request.date_to, 
                    request.include_inactive
                )
                
                # Generate file if CSV format requested
                download_url = None
                file_size = None
                
                if request.format == ReportFormat.CSV:
                    csv_content = self.generate_csv_report(detailed_data)
                    # In a real implementation, you'd save this to a file storage service
                    # and return a download URL
                    file_size = len(csv_content.encode('utf-8'))
                
                return ReportResponse(
                    success=True,
                    report_type=request.report_type,
                    format=request.format,
                    generated_at=datetime.utcnow(),
                    detailed_data=detailed_data,
                    download_url=download_url,
                    file_size=file_size
                )
            
            else:
                return ReportResponse(
                    success=False,
                    report_type=request.report_type,
                    format=request.format,
                    generated_at=datetime.utcnow(),
                    error_message=f"Unsupported report type: {request.report_type}"
                )
                
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return ReportResponse(
                success=False,
                report_type=request.report_type,
                format=request.format,
                generated_at=datetime.utcnow(),
                error_message=str(e)
            )
