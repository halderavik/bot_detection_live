"""
Aggregation service for hierarchical data analysis.

This service provides aggregated metrics at different hierarchy levels:
- Survey level: Aggregates across all platforms, respondents, and sessions
- Platform level: Aggregates across all respondents and sessions for a platform
- Respondent level: Aggregates across all sessions for a respondent
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload
import logging
import statistics

from app.models import Session, BehaviorData, DetectionResult, SurveyResponse, GridResponse, TimingAnalysis
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class AggregationService:
    """Service for calculating aggregated metrics at hierarchical levels."""
    
    def __init__(self):
        """Initialize the aggregation service."""
        self.logger = logger
    
    async def get_survey_aggregation(
        self, 
        survey_id: str, 
        db: AsyncSession,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics for a survey.
        
        Args:
            survey_id: Survey identifier
            db: Database session
            date_from: Optional start date filter
            date_to: Optional end date filter
            
        Returns:
            Dictionary with aggregated survey metrics
        """
        try:
            # Build base query conditions
            conditions = [Session.survey_id == survey_id]
            
            if date_from:
                conditions.append(Session.created_at >= date_from)
            if date_to:
                conditions.append(Session.created_at <= date_to)
            
            # Get session counts
            session_query = select(func.count(Session.id)).where(and_(*conditions))
            result = await db.execute(session_query)
            total_sessions = result.scalar() or 0
            
            # Get unique respondents count
            respondent_query = (
                select(func.count(func.distinct(Session.respondent_id)))
                .where(and_(*conditions, Session.respondent_id.isnot(None)))
            )
            result = await db.execute(respondent_query)
            total_respondents = result.scalar() or 0
            
            # Get unique platforms count
            platform_query = (
                select(func.count(func.distinct(Session.platform_id)))
                .where(and_(*conditions, Session.platform_id.isnot(None)))
            )
            result = await db.execute(platform_query)
            total_platforms = result.scalar() or 0
            
            # Get platform distribution
            platform_dist_query = (
                select(
                    Session.platform_id,
                    func.count(Session.id).label('count')
                )
                .where(and_(*conditions, Session.platform_id.isnot(None)))
                .group_by(Session.platform_id)
            )
            result = await db.execute(platform_dist_query)
            platform_distribution = {
                row.platform_id: row.count 
                for row in result
            }
            
            # Get bot detection metrics
            bot_query = (
                select(
                    func.count(DetectionResult.id).label('total_detections'),
                    func.sum(case((DetectionResult.is_bot == True, 1), else_=0)).label('bot_count'),
                    func.avg(DetectionResult.confidence_score).label('avg_confidence')
                )
                .join(Session, DetectionResult.session_id == Session.id)
                .where(and_(*conditions))
            )
            result = await db.execute(bot_query)
            bot_row = result.first()
            
            total_detections = bot_row.total_detections or 0
            bot_count = bot_row.bot_count or 0
            avg_confidence = float(bot_row.avg_confidence) if bot_row.avg_confidence else None
            bot_rate = (bot_count / total_detections * 100) if total_detections > 0 else 0
            
            # Get risk level distribution
            risk_query = (
                select(
                    DetectionResult.risk_level,
                    func.count(DetectionResult.id).label('count')
                )
                .join(Session, DetectionResult.session_id == Session.id)
                .where(and_(*conditions, DetectionResult.risk_level.isnot(None)))
                .group_by(DetectionResult.risk_level)
            )
            result = await db.execute(risk_query)
            risk_distribution = {
                row.risk_level: row.count 
                for row in result
            }
            
            # Get event counts
            event_query = (
                select(func.count(BehaviorData.id))
                .join(Session, BehaviorData.session_id == Session.id)
                .where(and_(*conditions))
            )
            result = await db.execute(event_query)
            total_events = result.scalar() or 0
            
            # Get text quality metrics
            text_quality_query = (
                select(
                    func.count(SurveyResponse.id).label('total_responses'),
                    func.avg(SurveyResponse.quality_score).label('avg_quality'),
                    func.sum(case((SurveyResponse.is_flagged == True, 1), else_=0)).label('flagged_count')
                )
                .join(Session, SurveyResponse.session_id == Session.id)
                .where(and_(*conditions))
            )
            result = await db.execute(text_quality_query)
            text_row = result.first()
            
            total_responses = text_row.total_responses or 0
            avg_quality_score = float(text_row.avg_quality) if text_row.avg_quality else None
            flagged_count = text_row.flagged_count or 0
            flagged_percentage = (flagged_count / total_responses * 100) if total_responses > 0 else 0
            
            # Get date range
            date_range_query = (
                select(
                    func.min(Session.created_at).label('first_session'),
                    func.max(Session.created_at).label('last_session')
                )
                .where(and_(*conditions))
            )
            result = await db.execute(date_range_query)
            date_row = result.first()
            
            return {
                "survey_id": survey_id,
                "total_sessions": total_sessions,
                "total_respondents": total_respondents,
                "total_platforms": total_platforms,
                "platform_distribution": platform_distribution,
                "bot_detection": {
                    "total_detections": total_detections,
                    "bot_count": bot_count,
                    "human_count": total_detections - bot_count,
                    "bot_rate": round(bot_rate, 2),
                    "avg_confidence": round(avg_confidence, 3) if avg_confidence else None
                },
                "risk_distribution": risk_distribution,
                "events": {
                    "total_events": total_events,
                    "avg_events_per_session": round(total_events / total_sessions, 2) if total_sessions > 0 else 0
                },
                "text_quality": {
                    "total_responses": total_responses,
                    "avg_quality_score": round(avg_quality_score, 2) if avg_quality_score else None,
                    "flagged_count": flagged_count,
                    "flagged_percentage": round(flagged_percentage, 2)
                },
                "date_range": {
                    "first_session": date_row.first_session.isoformat() if date_row.first_session else None,
                    "last_session": date_row.last_session.isoformat() if date_row.last_session else None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting survey aggregation: {e}")
            raise
    
    async def get_platform_aggregation(
        self,
        survey_id: str,
        platform_id: str,
        db: AsyncSession,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics for a platform within a survey.
        
        Args:
            survey_id: Survey identifier
            platform_id: Platform identifier
            db: Database session
            date_from: Optional start date filter
            date_to: Optional end date filter
            
        Returns:
            Dictionary with aggregated platform metrics
        """
        try:
            # Build base query conditions
            conditions = [
                Session.survey_id == survey_id,
                Session.platform_id == platform_id
            ]
            
            if date_from:
                conditions.append(Session.created_at >= date_from)
            if date_to:
                conditions.append(Session.created_at <= date_to)
            
            # Get session counts
            session_query = select(func.count(Session.id)).where(and_(*conditions))
            result = await db.execute(session_query)
            total_sessions = result.scalar() or 0
            
            # Get unique respondents count
            respondent_query = (
                select(func.count(func.distinct(Session.respondent_id)))
                .where(and_(*conditions, Session.respondent_id.isnot(None)))
            )
            result = await db.execute(respondent_query)
            total_respondents = result.scalar() or 0
            
            # Get bot detection metrics
            bot_query = (
                select(
                    func.count(DetectionResult.id).label('total_detections'),
                    func.sum(case((DetectionResult.is_bot == True, 1), else_=0)).label('bot_count'),
                    func.avg(DetectionResult.confidence_score).label('avg_confidence')
                )
                .join(Session, DetectionResult.session_id == Session.id)
                .where(and_(*conditions))
            )
            result = await db.execute(bot_query)
            bot_row = result.first()
            
            total_detections = bot_row.total_detections or 0
            bot_count = bot_row.bot_count or 0
            avg_confidence = float(bot_row.avg_confidence) if bot_row.avg_confidence else None
            bot_rate = (bot_count / total_detections * 100) if total_detections > 0 else 0
            
            # Get event counts
            event_query = (
                select(func.count(BehaviorData.id))
                .join(Session, BehaviorData.session_id == Session.id)
                .where(and_(*conditions))
            )
            result = await db.execute(event_query)
            total_events = result.scalar() or 0
            
            # Get text quality metrics
            text_quality_query = (
                select(
                    func.count(SurveyResponse.id).label('total_responses'),
                    func.avg(SurveyResponse.quality_score).label('avg_quality'),
                    func.sum(case((SurveyResponse.is_flagged == True, 1), else_=0)).label('flagged_count')
                )
                .join(Session, SurveyResponse.session_id == Session.id)
                .where(and_(*conditions))
            )
            result = await db.execute(text_quality_query)
            text_row = result.first()
            
            total_responses = text_row.total_responses or 0
            avg_quality_score = float(text_row.avg_quality) if text_row.avg_quality else None
            flagged_count = text_row.flagged_count or 0
            flagged_percentage = (flagged_count / total_responses * 100) if total_responses > 0 else 0
            
            return {
                "survey_id": survey_id,
                "platform_id": platform_id,
                "total_sessions": total_sessions,
                "total_respondents": total_respondents,
                "bot_detection": {
                    "total_detections": total_detections,
                    "bot_count": bot_count,
                    "human_count": total_detections - bot_count,
                    "bot_rate": round(bot_rate, 2),
                    "avg_confidence": round(avg_confidence, 3) if avg_confidence else None
                },
                "events": {
                    "total_events": total_events,
                    "avg_events_per_session": round(total_events / total_sessions, 2) if total_sessions > 0 else 0
                },
                "text_quality": {
                    "total_responses": total_responses,
                    "avg_quality_score": round(avg_quality_score, 2) if avg_quality_score else None,
                    "flagged_count": flagged_count,
                    "flagged_percentage": round(flagged_percentage, 2)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting platform aggregation: {e}")
            raise
    
    async def get_respondent_aggregation(
        self,
        survey_id: str,
        platform_id: str,
        respondent_id: str,
        db: AsyncSession,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics for a respondent across all their sessions.
        
        Args:
            survey_id: Survey identifier
            platform_id: Platform identifier
            respondent_id: Respondent identifier
            db: Database session
            date_from: Optional start date filter
            date_to: Optional end date filter
            
        Returns:
            Dictionary with aggregated respondent metrics
        """
        try:
            # Build base query conditions
            conditions = [
                Session.survey_id == survey_id,
                Session.platform_id == platform_id,
                Session.respondent_id == respondent_id
            ]
            
            if date_from:
                conditions.append(Session.created_at >= date_from)
            if date_to:
                conditions.append(Session.created_at <= date_to)
            
            # Get all sessions for this respondent
            sessions_query = (
                select(Session)
                .where(and_(*conditions))
                .order_by(Session.created_at.desc())
            )
            result = await db.execute(sessions_query)
            sessions = result.scalars().all()
            
            total_sessions = len(sessions)
            session_ids = [s.id for s in sessions]
            
            if total_sessions == 0:
                return {
                    "survey_id": survey_id,
                    "platform_id": platform_id,
                    "respondent_id": respondent_id,
                    "total_sessions": 0,
                    "sessions": [],
                    "bot_detection": {},
                    "text_quality": {},
                    "session_timeline": []
                }
            
            # Get bot detection metrics across all sessions
            bot_query = (
                select(
                    func.count(DetectionResult.id).label('total_detections'),
                    func.sum(case((DetectionResult.is_bot == True, 1), else_=0)).label('bot_count'),
                    func.avg(DetectionResult.confidence_score).label('avg_confidence'),
                    func.max(DetectionResult.confidence_score).label('max_confidence'),
                    func.min(DetectionResult.confidence_score).label('min_confidence')
                )
                .where(DetectionResult.session_id.in_(session_ids))
            )
            result = await db.execute(bot_query)
            bot_row = result.first()
            
            total_detections = bot_row.total_detections or 0
            bot_count = bot_row.bot_count or 0
            avg_confidence = float(bot_row.avg_confidence) if bot_row.avg_confidence else None
            max_confidence = float(bot_row.max_confidence) if bot_row.max_confidence else None
            min_confidence = float(bot_row.min_confidence) if bot_row.min_confidence else None
            bot_rate = (bot_count / total_detections * 100) if total_detections > 0 else 0
            
            # Get latest detection result for overall risk assessment
            latest_detection_query = (
                select(DetectionResult)
                .where(DetectionResult.session_id.in_(session_ids))
                .order_by(DetectionResult.created_at.desc())
                .limit(1)
            )
            result = await db.execute(latest_detection_query)
            latest_detection = result.scalar_one_or_none()
            
            # Get text quality metrics across all sessions
            text_quality_query = (
                select(
                    func.count(SurveyResponse.id).label('total_responses'),
                    func.avg(SurveyResponse.quality_score).label('avg_quality'),
                    func.sum(case((SurveyResponse.is_flagged == True, 1), else_=0)).label('flagged_count')
                )
                .where(SurveyResponse.session_id.in_(session_ids))
            )
            result = await db.execute(text_quality_query)
            text_row = result.first()
            
            total_responses = text_row.total_responses or 0
            avg_quality_score = float(text_row.avg_quality) if text_row.avg_quality else None
            flagged_count = text_row.flagged_count or 0
            flagged_percentage = (flagged_count / total_responses * 100) if total_responses > 0 else 0
            
            # Build session timeline
            session_timeline = [
                {
                    "session_id": s.id,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "is_active": s.is_active,
                    "is_completed": s.is_completed
                }
                for s in sessions
            ]
            
            # Get session summaries
            session_summaries = []
            for session in sessions:
                # Get event count
                event_count_query = select(func.count(BehaviorData.id)).where(BehaviorData.session_id == session.id)
                result = await db.execute(event_count_query)
                event_count = result.scalar() or 0
                
                # Get latest detection
                latest_det_query = (
                    select(DetectionResult)
                    .where(DetectionResult.session_id == session.id)
                    .order_by(DetectionResult.created_at.desc())
                    .limit(1)
                )
                result = await db.execute(latest_det_query)
                latest_det = result.scalar_one_or_none()
                
                session_summaries.append({
                    "session_id": session.id,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "event_count": event_count,
                    "latest_detection": {
                        "is_bot": latest_det.is_bot if latest_det else None,
                        "confidence_score": float(latest_det.confidence_score) if latest_det and latest_det.confidence_score else None,
                        "risk_level": latest_det.risk_level if latest_det else None
                    } if latest_det else None
                })
            
            return {
                "survey_id": survey_id,
                "platform_id": platform_id,
                "respondent_id": respondent_id,
                "total_sessions": total_sessions,
                "sessions": session_summaries,
                "bot_detection": {
                    "total_detections": total_detections,
                    "bot_count": bot_count,
                    "human_count": total_detections - bot_count,
                    "bot_rate": round(bot_rate, 2),
                    "avg_confidence": round(avg_confidence, 3) if avg_confidence else None,
                    "max_confidence": round(max_confidence, 3) if max_confidence else None,
                    "min_confidence": round(min_confidence, 3) if min_confidence else None,
                    "overall_risk": latest_detection.risk_level if latest_detection else None
                },
                "text_quality": {
                    "total_responses": total_responses,
                    "avg_quality_score": round(avg_quality_score, 2) if avg_quality_score else None,
                    "flagged_count": flagged_count,
                    "flagged_percentage": round(flagged_percentage, 2)
                },
                "session_timeline": session_timeline
            }
            
        except Exception as e:
            self.logger.error(f"Error getting respondent aggregation: {e}")
            raise
    
    async def list_surveys(
        self,
        db: AsyncSession,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all surveys with basic aggregated stats.
        
        Args:
            db: Database session
            limit: Maximum number of surveys to return
            offset: Offset for pagination
            
        Returns:
            List of survey summaries
        """
        try:
            # Get unique surveys with basic counts
            query = (
                select(
                    Session.survey_id,
                    func.count(func.distinct(Session.respondent_id)).label('respondent_count'),
                    func.count(Session.id).label('session_count'),
                    func.min(Session.created_at).label('first_session'),
                    func.max(Session.created_at).label('last_session')
                )
                .where(Session.survey_id.isnot(None))
                .group_by(Session.survey_id)
                .order_by(func.count(Session.id).desc())
                .limit(limit)
                .offset(offset)
            )
            
            result = await db.execute(query)
            surveys = []
            
            for row in result:
                # Get bot count for this survey
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
                    "respondent_count": row.respondent_count,
                    "session_count": row.session_count,
                    "bot_count": bot_count,
                    "human_count": row.session_count - bot_count,
                    "bot_rate": round((bot_count / row.session_count * 100), 2) if row.session_count > 0 else 0,
                    "first_session": row.first_session.isoformat() if row.first_session else None,
                    "last_session": row.last_session.isoformat() if row.last_session else None
                })
            
            return surveys
            
        except Exception as e:
            self.logger.error(f"Error listing surveys: {e}")
            raise
    
    async def list_platforms(
        self,
        survey_id: str,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        List all platforms for a survey.
        
        Args:
            survey_id: Survey identifier
            db: Database session
            
        Returns:
            List of platform summaries
        """
        try:
            query = (
                select(
                    Session.platform_id,
                    func.count(func.distinct(Session.respondent_id)).label('respondent_count'),
                    func.count(Session.id).label('session_count')
                )
                .where(
                    and_(
                        Session.survey_id == survey_id,
                        Session.platform_id.isnot(None)
                    )
                )
                .group_by(Session.platform_id)
                .order_by(func.count(Session.id).desc())
            )
            
            result = await db.execute(query)
            platforms = []
            
            for row in result:
                platforms.append({
                    "platform_id": row.platform_id,
                    "respondent_count": row.respondent_count,
                    "session_count": row.session_count
                })
            
            return platforms
            
        except Exception as e:
            self.logger.error(f"Error listing platforms: {e}")
            raise
    
    async def list_respondents(
        self,
        survey_id: str,
        platform_id: str,
        db: AsyncSession,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all respondents for a platform.
        
        Args:
            survey_id: Survey identifier
            platform_id: Platform identifier
            db: Database session
            limit: Maximum number of respondents to return
            offset: Offset for pagination
            
        Returns:
            List of respondent summaries
        """
        try:
            query = (
                select(
                    Session.respondent_id,
                    func.count(Session.id).label('session_count'),
                    func.min(Session.created_at).label('first_session'),
                    func.max(Session.created_at).label('last_session')
                )
                .where(
                    and_(
                        Session.survey_id == survey_id,
                        Session.platform_id == platform_id,
                        Session.respondent_id.isnot(None)
                    )
                )
                .group_by(Session.respondent_id)
                .order_by(func.count(Session.id).desc())
                .limit(limit)
                .offset(offset)
            )
            
            result = await db.execute(query)
            respondents = []
            
            for row in result:
                # Get bot count for this respondent
                bot_count_query = (
                    select(func.count(DetectionResult.id))
                    .join(Session, DetectionResult.session_id == Session.id)
                    .where(
                        and_(
                            Session.survey_id == survey_id,
                            Session.platform_id == platform_id,
                            Session.respondent_id == row.respondent_id,
                            DetectionResult.is_bot == True
                        )
                    )
                )
                bot_result = await db.execute(bot_count_query)
                bot_count = bot_result.scalar() or 0
                
                respondents.append({
                    "respondent_id": row.respondent_id,
                    "session_count": row.session_count,
                    "bot_count": bot_count,
                    "human_count": row.session_count - bot_count,
                    "first_session": row.first_session.isoformat() if row.first_session else None,
                    "last_session": row.last_session.isoformat() if row.last_session else None
                })
            
            return respondents
            
        except Exception as e:
            self.logger.error(f"Error listing respondents: {e}")
            raise
    
    async def get_grid_analysis_summary(
        self,
        survey_id: str,
        platform_id: Optional[str] = None,
        respondent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        db: AsyncSession = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get grid analysis summary at specified hierarchy level.
        
        Args:
            survey_id: Survey identifier
            platform_id: Optional platform identifier
            respondent_id: Optional respondent identifier
            session_id: Optional session identifier
            db: Database session
            date_from: Optional start date filter
            date_to: Optional end date filter
            
        Returns:
            Dictionary with grid analysis summary statistics
        """
        try:
            # Build query conditions
            conditions = [GridResponse.survey_id == survey_id]
            
            if platform_id:
                conditions.append(GridResponse.platform_id == platform_id)
            if respondent_id:
                conditions.append(GridResponse.respondent_id == respondent_id)
            if session_id:
                conditions.append(GridResponse.session_id == session_id)
            if date_from:
                conditions.append(GridResponse.created_at >= date_from)
            if date_to:
                conditions.append(GridResponse.created_at <= date_to)
            
            # Get total grid responses
            total_query = select(func.count(GridResponse.id)).where(and_(*conditions))
            result = await db.execute(total_query)
            total_responses = result.scalar() or 0
            
            if total_responses == 0:
                return {
                    "survey_id": survey_id,
                    "platform_id": platform_id,
                    "respondent_id": respondent_id,
                    "session_id": session_id,
                    "total_responses": 0,
                    "straight_lined_count": 0,
                    "straight_lined_percentage": 0.0,
                    "pattern_distribution": {},
                    "avg_variance_score": 0.0,
                    "avg_satisficing_score": 0.0,
                    "unique_questions": 0
                }
            
            # Get straight-lining count
            straight_lined_query = select(func.count(GridResponse.id)).where(
                and_(*conditions, GridResponse.is_straight_lined == True)
            )
            result = await db.execute(straight_lined_query)
            straight_lined_count = result.scalar() or 0
            
            # Get pattern distribution
            pattern_query = (
                select(
                    GridResponse.pattern_type,
                    func.count(GridResponse.id).label('count')
                )
                .where(and_(*conditions, GridResponse.pattern_type.isnot(None)))
                .group_by(GridResponse.pattern_type)
            )
            result = await db.execute(pattern_query)
            pattern_distribution = {row.pattern_type: row.count for row in result}
            
            # Get average variance and satisficing scores
            avg_scores_query = (
                select(
                    func.avg(GridResponse.variance_score).label('avg_variance'),
                    func.avg(GridResponse.satisficing_score).label('avg_satisficing')
                )
                .where(and_(*conditions))
            )
            result = await db.execute(avg_scores_query)
            avg_row = result.first()
            avg_variance = float(avg_row.avg_variance) if avg_row.avg_variance else 0.0
            avg_satisficing = float(avg_row.avg_satisficing) if avg_row.avg_satisficing else 0.0
            
            # Get unique questions count
            unique_questions_query = (
                select(func.count(func.distinct(GridResponse.question_id)))
                .where(and_(*conditions))
            )
            result = await db.execute(unique_questions_query)
            unique_questions = result.scalar() or 0
            
            return {
                "survey_id": survey_id,
                "platform_id": platform_id,
                "respondent_id": respondent_id,
                "session_id": session_id,
                "total_responses": total_responses,
                "straight_lined_count": straight_lined_count,
                "straight_lined_percentage": (straight_lined_count / total_responses * 100) if total_responses > 0 else 0.0,
                "pattern_distribution": pattern_distribution,
                "avg_variance_score": avg_variance,
                "avg_satisficing_score": avg_satisficing,
                "unique_questions": unique_questions
            }
            
        except Exception as e:
            self.logger.error(f"Error getting grid analysis summary: {e}")
            raise
    
    async def get_timing_analysis_summary(
        self,
        survey_id: str,
        platform_id: Optional[str] = None,
        respondent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        db: AsyncSession = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get timing analysis summary at specified hierarchy level.
        
        Args:
            survey_id: Survey identifier
            platform_id: Optional platform identifier
            respondent_id: Optional respondent identifier
            session_id: Optional session identifier
            db: Database session
            date_from: Optional start date filter
            date_to: Optional end date filter
            
        Returns:
            Dictionary with timing analysis summary statistics
        """
        try:
            # Build query conditions
            conditions = [TimingAnalysis.survey_id == survey_id]
            
            if platform_id:
                conditions.append(TimingAnalysis.platform_id == platform_id)
            if respondent_id:
                conditions.append(TimingAnalysis.respondent_id == respondent_id)
            if session_id:
                conditions.append(TimingAnalysis.session_id == session_id)
            if date_from:
                conditions.append(TimingAnalysis.created_at >= date_from)
            if date_to:
                conditions.append(TimingAnalysis.created_at <= date_to)
            
            # Get total timing analyses
            total_query = select(func.count(TimingAnalysis.id)).where(and_(*conditions))
            result = await db.execute(total_query)
            total_analyses = result.scalar() or 0
            
            if total_analyses == 0:
                return {
                    "survey_id": survey_id,
                    "platform_id": platform_id,
                    "respondent_id": respondent_id,
                    "session_id": session_id,
                    "total_analyses": 0,
                    "speeders_count": 0,
                    "speeders_percentage": 0.0,
                    "flatliners_count": 0,
                    "flatliners_percentage": 0.0,
                    "anomalies_count": 0,
                    "avg_response_time_ms": 0.0,
                    "median_response_time_ms": 0.0,
                    "unique_questions": 0
                }
            
            # Get speeders count
            speeders_query = select(func.count(TimingAnalysis.id)).where(
                and_(*conditions, TimingAnalysis.is_speeder == True)
            )
            result = await db.execute(speeders_query)
            speeders_count = result.scalar() or 0
            
            # Get flatliners count
            flatliners_query = select(func.count(TimingAnalysis.id)).where(
                and_(*conditions, TimingAnalysis.is_flatliner == True)
            )
            result = await db.execute(flatliners_query)
            flatliners_count = result.scalar() or 0
            
            # Get anomalies count (z-score > 2.5)
            anomalies_query = select(func.count(TimingAnalysis.id)).where(
                and_(*conditions, func.abs(TimingAnalysis.anomaly_score) > 2.5)
            )
            result = await db.execute(anomalies_query)
            anomalies_count = result.scalar() or 0
            
            # Get average response time
            avg_time_query = (
                select(func.avg(TimingAnalysis.question_time_ms).label('avg_time'))
                .where(and_(*conditions))
            )
            result = await db.execute(avg_time_query)
            avg_time = float(result.scalar()) if result.scalar() else 0.0
            
            # Get median response time (fetch all times and calculate in Python for simplicity)
            median_query = select(TimingAnalysis.question_time_ms).where(and_(*conditions))
            result = await db.execute(median_query)
            times = [row[0] for row in result if row[0] is not None]
            median_time = statistics.median(times) if times else 0.0
            
            # Get unique questions count
            unique_questions_query = (
                select(func.count(func.distinct(TimingAnalysis.question_id)))
                .where(and_(*conditions))
            )
            result = await db.execute(unique_questions_query)
            unique_questions = result.scalar() or 0
            
            return {
                "survey_id": survey_id,
                "platform_id": platform_id,
                "respondent_id": respondent_id,
                "session_id": session_id,
                "total_analyses": total_analyses,
                "speeders_count": speeders_count,
                "speeders_percentage": (speeders_count / total_analyses * 100) if total_analyses > 0 else 0.0,
                "flatliners_count": flatliners_count,
                "flatliners_percentage": (flatliners_count / total_analyses * 100) if total_analyses > 0 else 0.0,
                "anomalies_count": anomalies_count,
                "anomalies_percentage": (anomalies_count / total_analyses * 100) if total_analyses > 0 else 0.0,
                "avg_response_time_ms": avg_time,
                "median_response_time_ms": median_time,
                "unique_questions": unique_questions
            }
            
        except Exception as e:
            self.logger.error(f"Error getting timing analysis summary: {e}")
            raise

