"""
Timing Analysis Service for detecting speeders, flatliners, and timing anomalies.

This service analyzes response times to detect:
- Speeders (responses too fast, < 2 seconds)
- Flatliners (responses too slow, > 5 minutes)
- Statistical timing anomalies (z-score outliers)
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete
from datetime import datetime
import statistics
import logging

from app.models import SurveyQuestion, SurveyResponse, TimingAnalysis, Session
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class TimingAnalysisService:
    """Service for analyzing response timing patterns."""
    
    def __init__(self):
        """Initialize timing analysis service."""
        self.speeder_threshold_ms = 2000  # 2 seconds
        self.flatliner_threshold_ms = 300000  # 5 minutes (300 seconds)
        self.anomaly_z_score_threshold = 2.5  # Z-score threshold for outliers
    
    def detect_speeders(self, responses: List[Dict], threshold_ms: int = None) -> List[Dict]:
        """
        Detect speeder responses (too fast).
        
        Args:
            responses: List of response dictionaries with 'response_time_ms' key
            threshold_ms: Optional custom threshold (defaults to 2000ms)
            
        Returns:
            List of speeder response dictionaries
        """
        if threshold_ms is None:
            threshold_ms = self.speeder_threshold_ms
        
        speeders = []
        for resp in responses:
            response_time = resp.get("response_time_ms")
            if response_time is not None and response_time < threshold_ms:
                speeders.append({
                    **resp,
                    "is_speeder": True,
                    "threshold_used": threshold_ms
                })
        
        return speeders
    
    def detect_flatliners(self, responses: List[Dict], threshold_ms: int = None) -> List[Dict]:
        """
        Detect flatliner responses (too slow).
        
        Args:
            responses: List of response dictionaries with 'response_time_ms' key
            threshold_ms: Optional custom threshold (defaults to 300000ms)
            
        Returns:
            List of flatliner response dictionaries
        """
        if threshold_ms is None:
            threshold_ms = self.flatliner_threshold_ms
        
        flatliners = []
        for resp in responses:
            response_time = resp.get("response_time_ms")
            if response_time is not None and response_time > threshold_ms:
                flatliners.append({
                    **resp,
                    "is_flatliner": True,
                    "threshold_used": threshold_ms
                })
        
        return flatliners
    
    def calculate_adaptive_thresholds(self, responses: List[Dict]) -> Dict[str, float]:
        """
        Calculate adaptive thresholds based on response time distribution.
        
        Args:
            responses: List of response dictionaries with 'response_time_ms'
            
        Returns:
            Dict with 'speeder_threshold', 'flatliner_threshold', 'mean', 'std_dev'
        """
        if not responses:
            return {
                "speeder_threshold": self.speeder_threshold_ms,
                "flatliner_threshold": self.flatliner_threshold_ms,
                "mean": 0.0,
                "std_dev": 0.0
            }
        
        # Extract response times
        times = [r.get("response_time_ms") for r in responses if r.get("response_time_ms") is not None]
        
        if len(times) < 2:
            return {
                "speeder_threshold": self.speeder_threshold_ms,
                "flatliner_threshold": self.flatliner_threshold_ms,
                "mean": times[0] if times else 0.0,
                "std_dev": 0.0
            }
        
        # Calculate statistics
        mean_time = statistics.mean(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        
        # Adaptive thresholds: mean - 2*std_dev for speeders, mean + 2*std_dev for flatliners
        # But ensure they're within reasonable bounds
        speeder_threshold = max(500, min(mean_time - 2 * std_dev, self.speeder_threshold_ms))
        flatliner_threshold = min(600000, max(mean_time + 2 * std_dev, self.flatliner_threshold_ms))
        
        return {
            "speeder_threshold": speeder_threshold,
            "flatliner_threshold": flatliner_threshold,
            "mean": mean_time,
            "std_dev": std_dev
        }
    
    def detect_timing_anomalies(self, responses: List[Dict]) -> List[Dict]:
        """
        Detect statistical timing anomalies using z-score.
        
        Args:
            responses: List of response dictionaries with 'response_time_ms'
            
        Returns:
            List of anomalous response dictionaries with 'anomaly_score' and 'anomaly_type'
        """
        if not responses or len(responses) < 3:
            return []
        
        # Extract response times
        times = []
        for resp in responses:
            time_ms = resp.get("response_time_ms")
            if time_ms is not None:
                times.append(time_ms)
        
        if len(times) < 3:
            return []
        
        # Calculate mean and standard deviation
        mean_time = statistics.mean(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        
        if std_dev == 0:
            return []
        
        # Calculate z-scores and identify anomalies
        anomalies = []
        for resp in responses:
            time_ms = resp.get("response_time_ms")
            if time_ms is not None:
                z_score = (time_ms - mean_time) / std_dev
                
                if abs(z_score) > self.anomaly_z_score_threshold:
                    anomaly_type = "speeder" if z_score < 0 else "flatliner"
                    anomalies.append({
                        **resp,
                        "anomaly_score": z_score,
                        "anomaly_type": anomaly_type,
                        "mean_time": mean_time,
                        "std_dev": std_dev
                    })
        
        return anomalies
    
    async def analyze_timing(self, session_id: str, db: AsyncSession) -> Dict[str, Any]:
        """
        Analyze timing for all responses in a session.
        
        Args:
            session_id: Session ID to analyze
            db: Database session
            
        Returns:
            Dict with timing analysis results
        """
        try:
            # Get session to extract hierarchical fields
            session_result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = session_result.scalar_one_or_none()
            
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Get all responses for this session
            responses_result = await db.execute(
                select(SurveyResponse, SurveyQuestion).join(
                    SurveyQuestion, SurveyResponse.question_id == SurveyQuestion.id
                ).where(
                    SurveyResponse.session_id == session_id
                )
            )
            responses_with_questions = responses_result.all()
            
            if not responses_with_questions:
                return {
                    "session_id": session_id,
                    "responses_analyzed": 0,
                    "analysis_results": []
                }
            
            # Convert to dict format
            response_dicts = []
            for resp, question in responses_with_questions:
                response_dicts.append({
                    "question_id": question.id,
                    "question_text": question.question_text,
                    "response_time_ms": resp.response_time_ms,
                    "response_id": resp.id
                })
            
            # Perform analysis
            speeders = self.detect_speeders(response_dicts)
            flatliners = self.detect_flatliners(response_dicts)
            anomalies = self.detect_timing_anomalies(response_dicts)
            adaptive_thresholds = self.calculate_adaptive_thresholds(response_dicts)
            
            # Store results
            analysis_results = []
            for resp_dict in response_dicts:
                question_id = resp_dict["question_id"]
                response_time = resp_dict.get("response_time_ms")
                
                if response_time is None:
                    continue
                
                # Determine if speeder/flatliner/anomaly
                is_speeder = any(s["question_id"] == question_id for s in speeders)
                is_flatliner = any(f["question_id"] == question_id for f in flatliners)
                
                anomaly_info = next(
                    (a for a in anomalies if a["question_id"] == question_id),
                    None
                )
                anomaly_score = anomaly_info["anomaly_score"] if anomaly_info else None
                anomaly_type = anomaly_info["anomaly_type"] if anomaly_info else None
                
                # Determine threshold used
                threshold_used = None
                if is_speeder:
                    threshold_used = adaptive_thresholds["speeder_threshold"]
                elif is_flatliner:
                    threshold_used = adaptive_thresholds["flatliner_threshold"]
                
                analysis_result = {
                    "question_id": question_id,
                    "question_text": resp_dict["question_text"],
                    "question_time_ms": response_time,
                    "is_speeder": is_speeder,
                    "is_flatliner": is_flatliner,
                    "threshold_used": threshold_used,
                    "anomaly_score": anomaly_score,
                    "anomaly_type": anomaly_type
                }
                
                analysis_results.append(analysis_result)
                
                # Store in database
                await self.store_timing_analysis(
                    session_id,
                    question_id,
                    analysis_result,
                    db
                )
            
            return {
                "session_id": session_id,
                "survey_id": session.survey_id,
                "platform_id": session.platform_id,
                "respondent_id": session.respondent_id,
                "responses_analyzed": len(response_dicts),
                "speeders_count": len(speeders),
                "flatliners_count": len(flatliners),
                "anomalies_count": len(anomalies),
                "adaptive_thresholds": adaptive_thresholds,
                "analysis_results": analysis_results
            }
            
        except Exception as e:
            logger.error(f"Error analyzing timing for session {session_id}: {e}")
            raise
    
    async def store_timing_analysis(
        self,
        session_id: str,
        question_id: str,
        analysis_result: Dict[str, Any],
        db: AsyncSession
    ) -> None:
        """
        Store timing analysis results in database.
        
        Args:
            session_id: Session ID
            question_id: Question ID
            analysis_result: Analysis results dictionary
            db: Database session
        """
        try:
            # Get session for hierarchical fields
            session_result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = session_result.scalar_one_or_none()
            
            if not session:
                return
            
            # Delete existing timing analysis for this question
            await db.execute(
                delete(TimingAnalysis).where(
                    and_(
                        TimingAnalysis.question_id == question_id,
                        TimingAnalysis.session_id == session_id
                    )
                )
            )
            
            # Create timing analysis record
            timing_analysis = TimingAnalysis(
                session_id=session_id,
                question_id=question_id,
                survey_id=session.survey_id,
                platform_id=session.platform_id,
                respondent_id=session.respondent_id,
                question_time_ms=analysis_result["question_time_ms"],
                is_speeder=analysis_result.get("is_speeder", False),
                is_flatliner=analysis_result.get("is_flatliner", False),
                threshold_used=analysis_result.get("threshold_used"),
                anomaly_score=analysis_result.get("anomaly_score"),
                anomaly_type=analysis_result.get("anomaly_type"),
                analyzed_at=datetime.utcnow()
            )
            db.add(timing_analysis)
            
            await db.commit()
            logger.info(f"Stored timing analysis for question {question_id}")
            
        except Exception as e:
            logger.error(f"Error storing timing analysis: {e}")
            await db.rollback()
            raise
