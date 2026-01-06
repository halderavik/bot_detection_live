"""
Fraud Detection Service.

This service implements fraud detection algorithms analyzing
IP addresses, device fingerprints, duplicate responses, geolocation,
and velocity patterns to identify duplicate and suspicious respondents.
"""

import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from app.utils.logger import setup_logger
from app.utils.fraud_helpers import (
    generate_device_fingerprint,
    calculate_text_similarity,
    extract_geolocation_from_ip,
    calculate_fraud_risk_level,
    calculate_weighted_fraud_score,
    calculate_ip_risk_score,
    calculate_fingerprint_risk_score,
    calculate_duplicate_response_risk_score,
    calculate_velocity_risk_score
)
from app.models import Session, BehaviorData, SurveyResponse, FraudIndicator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

logger = setup_logger(__name__)


class FraudDetectionService:
    """Service for detecting fraud and duplicate respondents."""
    
    def __init__(self):
        """Initialize the fraud detection service."""
        self.ip_analysis_weight = 0.25
        self.fingerprint_weight = 0.25
        self.duplicate_weight = 0.20
        self.geolocation_weight = 0.15
        self.velocity_weight = 0.15
    
    async def analyze_session_fraud(
        self,
        session: Session,
        behavior_data: List[BehaviorData],
        db: AsyncSession
    ) -> FraudIndicator:
        """
        Analyze a session for fraud indicators.
        
        Args:
            session: Session to analyze
            behavior_data: List of behavior data events
            db: Database session
            
        Returns:
            FraudIndicator: Fraud detection results
        """
        start_time = time.time()
        
        # Run all fraud detection methods
        ip_analysis = await self._analyze_ip_address(session, db)
        fingerprint_analysis = await self._analyze_device_fingerprint(session, behavior_data, db)
        duplicate_analysis = await self._analyze_duplicate_responses(session, db)
        geolocation_analysis = await self._analyze_geolocation(session, db)
        velocity_analysis = await self._analyze_velocity(session, db)
        
        # Calculate overall fraud score
        overall_fraud_score = calculate_weighted_fraud_score(
            ip_analysis["risk_score"],
            fingerprint_analysis["risk_score"],
            duplicate_analysis["risk_score"],
            geolocation_analysis["risk_score"],
            velocity_analysis["risk_score"]
        )
        
        # Determine if duplicate
        is_duplicate = overall_fraud_score >= 0.7
        
        # Collect flag reasons
        flag_reasons = {}
        if ip_analysis["risk_score"] >= 0.6:
            flag_reasons["ip_reuse"] = {
                "count": ip_analysis["usage_count"],
                "severity": "high" if ip_analysis["risk_score"] >= 0.8 else "medium"
            }
        if fingerprint_analysis["risk_score"] >= 0.5:
            flag_reasons["device_reuse"] = {
                "count": fingerprint_analysis["usage_count"],
                "severity": "high" if fingerprint_analysis["risk_score"] >= 0.7 else "medium"
            }
        if duplicate_analysis["risk_score"] >= 0.6:
            flag_reasons["duplicate_responses"] = {
                "count": duplicate_analysis["duplicate_count"],
                "severity": "high" if duplicate_analysis["risk_score"] >= 0.8 else "medium"
            }
        if geolocation_analysis["risk_score"] >= 0.7:
            flag_reasons["geolocation_inconsistency"] = {
                "severity": "high"
            }
        if velocity_analysis["risk_score"] >= 0.6:
            flag_reasons["high_velocity"] = {
                "responses_per_hour": velocity_analysis["responses_per_hour"],
                "severity": "high" if velocity_analysis["risk_score"] >= 0.8 else "medium"
            }
        
        # Create fraud indicator
        fraud_indicator = FraudIndicator(
            session_id=session.id,
            survey_id=session.survey_id,  # Denormalize hierarchical fields
            platform_id=session.platform_id,
            respondent_id=session.respondent_id,
            ip_address=session.ip_address,
            ip_usage_count=ip_analysis["usage_count"],
            ip_sessions_today=ip_analysis["sessions_today"],
            ip_risk_score=ip_analysis["risk_score"],
            ip_country_code=geolocation_analysis.get("country_code"),
            device_fingerprint=fingerprint_analysis["fingerprint"],
            fingerprint_usage_count=fingerprint_analysis["usage_count"],
            fingerprint_risk_score=fingerprint_analysis["risk_score"],
            response_similarity_score=duplicate_analysis.get("max_similarity", 0.0),
            duplicate_response_count=duplicate_analysis["duplicate_count"],
            geolocation_consistent=geolocation_analysis["consistent"],
            geolocation_risk_score=geolocation_analysis["risk_score"],
            responses_per_hour=velocity_analysis["responses_per_hour"],
            velocity_risk_score=velocity_analysis["risk_score"],
            overall_fraud_score=overall_fraud_score,
            is_duplicate=is_duplicate,
            fraud_confidence=overall_fraud_score,
            flag_reasons=flag_reasons if flag_reasons else None,
            analysis_details={
                "ip_analysis": ip_analysis,
                "fingerprint_analysis": fingerprint_analysis,
                "duplicate_analysis": duplicate_analysis,
                "geolocation_analysis": geolocation_analysis,
                "velocity_analysis": velocity_analysis,
                "processing_time_ms": (time.time() - start_time) * 1000
            }
        )
        
        # Store device fingerprint in session
        if fingerprint_analysis["fingerprint"]:
            session.device_fingerprint = fingerprint_analysis["fingerprint"]
        
        logger.info(
            f"Fraud analysis completed for session {session.id}: "
            f"score={overall_fraud_score:.3f}, is_duplicate={is_duplicate}"
        )
        
        return fraud_indicator
    
    async def _analyze_ip_address(self, session: Session, db: AsyncSession) -> Dict[str, Any]:
        """
        Analyze IP address for reuse patterns.
        
        Args:
            session: Session to analyze
            db: Database session
            
        Returns:
            Dict with IP analysis results
        """
        if not session.ip_address:
            return {
                "risk_score": 0.0,
                "usage_count": 0,
                "sessions_today": 0
            }
        
        # Count total sessions with this IP
        total_count_query = select(func.count(Session.id)).where(
            Session.ip_address == session.ip_address
        )
        total_result = await db.execute(total_count_query)
        usage_count = total_result.scalar() or 0
        
        # Count sessions from today
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count_query = select(func.count(Session.id)).where(
            and_(
                Session.ip_address == session.ip_address,
                Session.created_at >= today_start
            )
        )
        today_result = await db.execute(today_count_query)
        sessions_today = today_result.scalar() or 0
        
        # Calculate risk score
        risk_score = calculate_ip_risk_score(usage_count, sessions_today)
        
        return {
            "risk_score": risk_score,
            "usage_count": usage_count,
            "sessions_today": sessions_today
        }
    
    async def _analyze_device_fingerprint(
        self,
        session: Session,
        behavior_data: List[BehaviorData],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Analyze device fingerprint for reuse patterns.
        
        Args:
            session: Session to analyze
            behavior_data: List of behavior data events
            db: Database session
            
        Returns:
            Dict with fingerprint analysis results
        """
        # Generate fingerprint
        fingerprint = generate_device_fingerprint(session, behavior_data)
        
        if not fingerprint:
            return {
                "risk_score": 0.0,
                "usage_count": 0,
                "fingerprint": None
            }
        
        # Count sessions with matching fingerprint
        count_query = select(func.count(Session.id)).where(
            Session.device_fingerprint == fingerprint
        )
        count_result = await db.execute(count_query)
        usage_count = count_result.scalar() or 0
        
        # Calculate risk score
        risk_score = calculate_fingerprint_risk_score(usage_count)
        
        return {
            "risk_score": risk_score,
            "usage_count": usage_count,
            "fingerprint": fingerprint
        }
    
    async def _analyze_duplicate_responses(
        self,
        session: Session,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Analyze responses for duplicates across sessions.
        
        Args:
            session: Session to analyze
            db: Database session
            
        Returns:
            Dict with duplicate analysis results
        """
        if not session.survey_id:
            return {
                "risk_score": 0.0,
                "duplicate_count": 0,
                "max_similarity": 0.0
            }
        
        # Get responses for this session
        responses_query = select(SurveyResponse).where(
            SurveyResponse.session_id == session.id
        ).where(
            SurveyResponse.response_text.isnot(None)
        )
        responses_result = await db.execute(responses_query)
        session_responses = responses_result.scalars().all()
        
        if not session_responses:
            return {
                "risk_score": 0.0,
                "duplicate_count": 0,
                "max_similarity": 0.0
            }
        
        # Get responses from other sessions in same survey
        other_responses_query = select(SurveyResponse).join(
            Session, SurveyResponse.session_id == Session.id
        ).where(
            and_(
                Session.survey_id == session.survey_id,
                Session.id != session.id,
                SurveyResponse.response_text.isnot(None)
            )
        )
        other_responses_result = await db.execute(other_responses_query)
        other_responses = other_responses_result.scalars().all()
        
        # Compare responses for similarity
        max_similarity = 0.0
        duplicate_count = 0
        similarity_threshold = 0.70  # Consider duplicate if >70% similar
        
        for session_response in session_responses:
            if not session_response.response_text:
                continue
            
            for other_response in other_responses:
                if not other_response.response_text:
                    continue
                
                similarity = calculate_text_similarity(
                    session_response.response_text,
                    other_response.response_text
                )
                
                if similarity > max_similarity:
                    max_similarity = similarity
                
                if similarity >= similarity_threshold:
                    duplicate_count += 1
        
        # Calculate risk score
        risk_score = calculate_duplicate_response_risk_score(max_similarity)
        
        return {
            "risk_score": risk_score,
            "duplicate_count": duplicate_count,
            "max_similarity": max_similarity
        }
    
    async def _analyze_geolocation(
        self,
        session: Session,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Analyze geolocation consistency.
        
        Args:
            session: Session to analyze
            db: Database session
            
        Returns:
            Dict with geolocation analysis results
        """
        if not session.ip_address:
            return {
                "risk_score": 0.0,
                "consistent": True,
                "country_code": None
            }
        
        # Extract geolocation from IP
        geolocation = extract_geolocation_from_ip(session.ip_address)
        country_code = geolocation.get("country_code")
        
        # Check for impossible location changes
        # (same respondent_id with different countries in short time)
        if session.respondent_id and country_code:
            # Find other sessions from same respondent
            other_sessions_query = select(Session).where(
                and_(
                    Session.respondent_id == session.respondent_id,
                    Session.id != session.id,
                    Session.created_at >= session.created_at - timedelta(hours=1)
                )
            )
            other_sessions_result = await db.execute(other_sessions_query)
            other_sessions = other_sessions_result.scalars().all()
            
            for other_session in other_sessions:
                if other_session.ip_address:
                    other_geolocation = extract_geolocation_from_ip(other_session.ip_address)
                    other_country = other_geolocation.get("country_code")
                    
                    # If countries differ and it's within 1 hour, flag as inconsistent
                    if other_country and country_code != other_country:
                        return {
                            "risk_score": 0.9,
                            "consistent": False,
                            "country_code": country_code
                        }
        
        return {
            "risk_score": 0.0,
            "consistent": True,
            "country_code": country_code
        }
    
    async def _analyze_velocity(
        self,
        session: Session,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Analyze velocity (responses per time) patterns.
        
        Args:
            session: Session to analyze
            db: Database session
            
        Returns:
            Dict with velocity analysis results
        """
        # Calculate responses per hour for different identifiers
        one_hour_ago = session.created_at - timedelta(hours=1)
        
        # By IP address
        if session.ip_address:
            ip_count_query = select(func.count(Session.id)).where(
                and_(
                    Session.ip_address == session.ip_address,
                    Session.created_at >= one_hour_ago
                )
            )
            ip_count_result = await db.execute(ip_count_query)
            ip_sessions_per_hour = ip_count_result.scalar() or 0
        else:
            ip_sessions_per_hour = 0
        
        # By device fingerprint
        if session.device_fingerprint:
            fp_count_query = select(func.count(Session.id)).where(
                and_(
                    Session.device_fingerprint == session.device_fingerprint,
                    Session.created_at >= one_hour_ago
                )
            )
            fp_count_result = await db.execute(fp_count_query)
            fp_sessions_per_hour = fp_count_result.scalar() or 0
        else:
            fp_sessions_per_hour = 0
        
        # By respondent_id
        if session.respondent_id:
            resp_count_query = select(func.count(Session.id)).where(
                and_(
                    Session.respondent_id == session.respondent_id,
                    Session.created_at >= one_hour_ago
                )
            )
            resp_count_result = await db.execute(resp_count_query)
            resp_sessions_per_hour = resp_count_result.scalar() or 0
        else:
            resp_sessions_per_hour = 0
        
        # Use maximum of the three as the velocity metric
        responses_per_hour = max(ip_sessions_per_hour, fp_sessions_per_hour, resp_sessions_per_hour)
        
        # Calculate risk score
        risk_score = calculate_velocity_risk_score(responses_per_hour)
        
        return {
            "risk_score": risk_score,
            "responses_per_hour": float(responses_per_hour)
        }
