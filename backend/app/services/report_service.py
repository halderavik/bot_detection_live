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

from app.models import Session, BehaviorData, DetectionResult, SurveyResponse, SurveyQuestion, FraudIndicator, GridResponse, TimingAnalysis
from app.models.report_models import (
    SurveySummaryReport, DetailedReport, RespondentDetail,
    ReportRequest, ReportResponse, ReportType, ReportFormat
)
from app.services.aggregation_service import AggregationService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ReportService:
    """Service for generating survey reports."""
    
    def __init__(self):
        """Initialize the report service."""
        self.logger = logger
        self.aggregation_service = AggregationService()
    
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
                    },
                    fraud_summary=None,
                    grid_analysis_summary=None,
                    timing_analysis_summary=None
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
            
            # Fraud summary: aggregate fraud_indicators for sessions in scope
            session_ids = [s.id for s in sessions]
            fraud_summary = await self._aggregate_fraud_for_sessions(db, survey_id, session_ids)
            
            # Grid analysis summary: use aggregation service at survey level with date filter
            grid_analysis_summary = await self.aggregation_service.get_grid_analysis_summary(
                survey_id=survey_id,
                platform_id=None,
                respondent_id=None,
                session_id=None,
                db=db,
                date_from=date_from,
                date_to=date_to
            )
            
            # Timing analysis summary: use aggregation service at survey level with date filter
            timing_analysis_summary = await self.aggregation_service.get_timing_analysis_summary(
                survey_id=survey_id,
                platform_id=None,
                respondent_id=None,
                session_id=None,
                db=db,
                date_from=date_from,
                date_to=date_to
            )
            
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
                text_quality_summary=text_quality_summary,
                fraud_summary=fraud_summary,
                grid_analysis_summary=grid_analysis_summary,
                timing_analysis_summary=timing_analysis_summary
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
                respondent_detail = await self._create_respondent_detail(session, db)
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
    
    async def _aggregate_fraud_for_sessions(
        self, db: AsyncSession, survey_id: str, session_ids: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Aggregate fraud detection metrics for a set of session IDs.
        Returns the same structure as hierarchical fraud summary, or None if no indicators.
        """
        if not session_ids:
            return None
        try:
            fraud_query = (
                select(FraudIndicator)
                .where(
                    and_(
                        FraudIndicator.survey_id == survey_id,
                        FraudIndicator.session_id.in_(session_ids)
                    )
                )
            )
            fraud_result = await db.execute(fraud_query)
            fraud_indicators = fraud_result.scalars().all()
            if not fraud_indicators:
                return {
                    "total_sessions_analyzed": 0,
                    "total_sessions": len(session_ids),
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
            total_analyzed = len(fraud_indicators)
            duplicate_count = sum(1 for fi in fraud_indicators if fi.is_duplicate)
            risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
            high_risk_count = 0
            fraud_scores = []
            fraud_methods = {
                "ip_high_risk": 0,
                "fingerprint_high_risk": 0,
                "duplicate_responses": 0,
                "geolocation_inconsistent": 0,
                "high_velocity": 0
            }
            for fi in fraud_indicators:
                if fi.risk_level in risk_distribution:
                    risk_distribution[fi.risk_level] += 1
                if fi.overall_fraud_score and float(fi.overall_fraud_score) >= 0.7:
                    high_risk_count += 1
                if fi.overall_fraud_score:
                    fraud_scores.append(float(fi.overall_fraud_score))
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
            avg_fraud_score = sum(fraud_scores) / len(fraud_scores) if fraud_scores else None
            duplicate_rate = (duplicate_count / total_analyzed * 100) if total_analyzed > 0 else 0.0
            high_risk_rate = (high_risk_count / total_analyzed * 100) if total_analyzed > 0 else 0.0
            return {
                "total_sessions_analyzed": total_analyzed,
                "total_sessions": len(session_ids),
                "duplicate_sessions": duplicate_count,
                "high_risk_sessions": high_risk_count,
                "average_fraud_score": round(avg_fraud_score, 3) if avg_fraud_score else None,
                "duplicate_rate": round(duplicate_rate, 2),
                "high_risk_rate": round(high_risk_rate, 2),
                "risk_distribution": risk_distribution,
                "fraud_methods": fraud_methods
            }
        except Exception as e:
            self.logger.warning(f"Error aggregating fraud for report: {e}")
            return None
    
    async def _create_respondent_detail(self, session: Session, db: AsyncSession) -> RespondentDetail:
        """Create respondent detail from session data including fraud, grid, and timing."""
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
        
        # Get text quality data for this session and build responses of interest
        text_response_count = None
        avg_text_quality_score = None
        flagged_text_responses = None
        text_quality_percentage = None
        text_responses_of_interest = None
        try:
            text_query = select(SurveyResponse).where(SurveyResponse.session_id == session.id)
            text_result = await db.execute(text_query)
            text_responses = text_result.scalars().all()
            if text_responses:
                text_response_count = len(text_responses)
                scores = [r.quality_score for r in text_responses if r.quality_score is not None]
                avg_text_quality_score = sum(scores) / len(scores) if scores else None
                flagged_text_responses = sum(1 for r in text_responses if r.is_flagged)
                text_quality_percentage = (flagged_text_responses / text_response_count * 100) if text_response_count else None
                # Build text_responses_of_interest with question previews
                question_ids = list({r.question_id for r in text_responses})
                q_result = await db.execute(select(SurveyQuestion).where(SurveyQuestion.id.in_(question_ids)))
                questions_map = {q.id: q for q in q_result.scalars().all()}
                text_responses_of_interest = []
                for r in text_responses:
                    q = questions_map.get(r.question_id)
                    question_preview = (q.question_text[:197] + "...") if q and getattr(q, "question_text", None) and len(q.question_text) > 200 else (getattr(q, "question_text", None) or "")
                    response_preview = (r.response_text[:197] + "...") if len(r.response_text) > 200 else r.response_text
                    text_responses_of_interest.append({
                        "question_preview": question_preview or "",
                        "response_preview": response_preview,
                        "quality_score": r.quality_score,
                        "is_flagged": bool(r.is_flagged),
                        "flag_reasons": r.flag_reasons or {},
                    })
        except Exception:
            pass
        
        # Fraud: latest fraud indicator for this session
        fraud_score = None
        is_duplicate = None
        fraud_risk_level = None
        fraud_flag_reasons = None
        fraud_velocity_summary = None
        try:
            fraud_query = (
                select(FraudIndicator)
                .where(FraudIndicator.session_id == session.id)
                .order_by(FraudIndicator.created_at.desc())
            )
            fraud_row = await db.execute(fraud_query)
            fi = fraud_row.scalars().first()
            if fi:
                fraud_score = float(fi.overall_fraud_score) if fi.overall_fraud_score else None
                is_duplicate = fi.is_duplicate
                rl = getattr(fi, "risk_level", None)
                fraud_risk_level = rl if isinstance(rl, str) else None
                fraud_flag_reasons = fi.flag_reasons if isinstance(getattr(fi, "flag_reasons", None), dict) else None
                if getattr(fi, "responses_per_hour", None) is not None or getattr(fi, "velocity_risk_score", None) is not None:
                    fraud_velocity_summary = {
                        "responses_per_hour": float(fi.responses_per_hour) if fi.responses_per_hour is not None else None,
                        "velocity_risk_score": float(fi.velocity_risk_score) if fi.velocity_risk_score is not None else None,
                    }
        except Exception:
            pass
        
        # Grid: any straight-lining, avg variance for this session; build grid_explanation
        grid_straight_lining = None
        grid_variance_score = None
        grid_explanation = None
        try:
            grid_query = select(GridResponse).where(GridResponse.session_id == session.id)
            grid_result = await db.execute(grid_query)
            grid_rows = grid_result.scalars().all()
            if grid_rows:
                grid_straight_lining = any(gr.is_straight_lined for gr in grid_rows)
                variances = [gr.variance_score for gr in grid_rows if gr.variance_score is not None]
                grid_variance_score = sum(variances) / len(variances) if variances else None
                straight_lined_count = sum(1 for gr in grid_rows if gr.is_straight_lined)
                parts = []
                if straight_lined_count > 0:
                    parts.append(f"Straight-lined on {straight_lined_count} grid question(s)")
                if grid_variance_score is not None:
                    parts.append(f"variance {grid_variance_score:.2f}")
                grid_explanation = "; ".join(parts) if parts else None
        except Exception:
            pass
        
        # Timing: any speeder/flatliner, anomaly count for this session; build timing_explanation
        timing_speeder = None
        timing_flatliner = None
        timing_anomaly_count = None
        timing_explanation = None
        try:
            timing_speeder_query = select(func.count(TimingAnalysis.id)).where(
                and_(TimingAnalysis.session_id == session.id, TimingAnalysis.is_speeder == True)
            )
            timing_flatliner_query = select(func.count(TimingAnalysis.id)).where(
                and_(TimingAnalysis.session_id == session.id, TimingAnalysis.is_flatliner == True)
            )
            timing_anom_query = select(func.count(TimingAnalysis.id)).where(
                and_(TimingAnalysis.session_id == session.id, func.abs(TimingAnalysis.anomaly_score) > 2.5)
            )
            sr = await db.execute(timing_speeder_query)
            flr = await db.execute(timing_flatliner_query)
            ar = await db.execute(timing_anom_query)
            timing_anomaly_count = ar.scalar() or 0
            speeder_count = sr.scalar() or 0
            flatliner_count = flr.scalar() or 0
            timing_speeder = speeder_count > 0
            timing_flatliner = flatliner_count > 0
            timing_parts = []
            if speeder_count > 0:
                timing_parts.append(f"Speeder ({speeder_count} question(s))")
            if flatliner_count > 0:
                timing_parts.append(f"Flatliner ({flatliner_count} question(s))")
            if timing_anomaly_count and timing_anomaly_count > 0:
                timing_parts.append(f"{timing_anomaly_count} timing anomaly(ies)")
            timing_explanation = "; ".join(timing_parts) if timing_parts else None
        except Exception:
            pass
        
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
            text_quality_percentage=text_quality_percentage,
            fraud_score=fraud_score,
            is_duplicate=is_duplicate,
            fraud_risk_level=fraud_risk_level,
            grid_straight_lining=grid_straight_lining,
            grid_variance_score=float(grid_variance_score) if grid_variance_score is not None else None,
            timing_speeder=timing_speeder,
            timing_flatliner=timing_flatliner,
            timing_anomaly_count=timing_anomaly_count,
            text_responses_of_interest=text_responses_of_interest,
            fraud_flag_reasons=fraud_flag_reasons,
            fraud_velocity_summary=fraud_velocity_summary,
            grid_explanation=grid_explanation,
            timing_explanation=timing_explanation,
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
            
            # Write header (include new columns for responses of interest and decision reasons)
            header = [
                "Session ID", "Respondent ID", "Created At", "Last Activity",
                "Is Bot", "Confidence Score", "Risk Level", "Total Events",
                "Session Duration (min)", "Event Breakdown", "Method Scores",
                "Flagged Patterns", "Analysis Summary", "Bot Explanation",
                "Text Response Count", "Avg Text Quality Score", "Flagged Text Responses", "Text Quality Percentage",
                "Fraud Score", "Is Duplicate", "Fraud Risk Level",
                "Grid Straight Lining", "Grid Variance Score",
                "Timing Speeder", "Timing Flatliner", "Timing Anomaly Count",
                "Text Responses of Interest", "Fraud Flag Reasons", "Fraud Velocity Summary",
                "Grid Explanation", "Timing Explanation"
            ]
            writer.writerow(header)
            
            # Write data rows
            for respondent in detailed_report.respondents:
                # Sanitize string fields for CSV: replace newlines with space to avoid breaking rows
                def safe_str(s: Optional[str]) -> str:
                    if s is None:
                        return ""
                    return s.replace("\r", " ").replace("\n", " ").strip()
                text_responses_csv = json.dumps(respondent.text_responses_of_interest) if respondent.text_responses_of_interest else ""
                fraud_reasons_csv = json.dumps(respondent.fraud_flag_reasons) if respondent.fraud_flag_reasons else ""
                fraud_velocity_csv = json.dumps(respondent.fraud_velocity_summary) if respondent.fraud_velocity_summary else ""
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
                    safe_str(respondent.analysis_summary),
                    safe_str(respondent.bot_explanation),
                    respondent.text_response_count or 0,
                    f"{respondent.avg_text_quality_score:.1f}" if respondent.avg_text_quality_score else "N/A",
                    respondent.flagged_text_responses or 0,
                    f"{respondent.text_quality_percentage:.1f}%" if respondent.text_quality_percentage else "N/A",
                    f"{respondent.fraud_score:.3f}" if respondent.fraud_score is not None else "",
                    "Yes" if respondent.is_duplicate else ("No" if respondent.is_duplicate is False else ""),
                    respondent.fraud_risk_level or "",
                    "Yes" if respondent.grid_straight_lining else ("No" if respondent.grid_straight_lining is False else ""),
                    f"{respondent.grid_variance_score:.3f}" if respondent.grid_variance_score is not None else "",
                    "Yes" if respondent.timing_speeder else ("No" if respondent.timing_speeder is False else ""),
                    "Yes" if respondent.timing_flatliner else ("No" if respondent.timing_flatliner is False else ""),
                    respondent.timing_anomaly_count if respondent.timing_anomaly_count is not None else "",
                    text_responses_csv,
                    fraud_reasons_csv,
                    fraud_velocity_csv,
                    safe_str(respondent.grid_explanation),
                    safe_str(respondent.timing_explanation),
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
