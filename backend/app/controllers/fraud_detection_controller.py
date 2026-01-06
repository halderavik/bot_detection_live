"""
Fraud Detection Controller.

This controller handles fraud detection API endpoints including
fraud analysis, IP tracking, device fingerprinting, and duplicate detection.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models import Session, FraudIndicator, BehaviorData, SurveyResponse
from app.services.fraud_detection_service import FraudDetectionService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class FraudDetectionController:
    """Controller for fraud detection endpoints."""
    
    def __init__(self):
        """Initialize the fraud detection controller."""
        self.router = APIRouter(prefix="/fraud", tags=["fraud"])
        self.fraud_service = FraudDetectionService()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes for fraud detection endpoints."""
        
        @self.router.get("/sessions/{session_id}")
        async def get_fraud_indicators(
            session_id: str,
            db: AsyncSession = Depends(get_db)
        ):
            """Get fraud indicators for a specific session."""
            try:
                # Validate session exists
                session_query = select(Session).where(Session.id == session_id)
                session_result = await db.execute(session_query)
                session = session_result.scalar_one_or_none()
                
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                # Get latest fraud indicator
                fraud_query = (
                    select(FraudIndicator)
                    .where(FraudIndicator.session_id == session_id)
                    .order_by(FraudIndicator.created_at.desc())
                    .limit(1)
                )
                fraud_result = await db.execute(fraud_query)
                fraud_indicator = fraud_result.scalar_one_or_none()
                
                if not fraud_indicator:
                    return {
                        "session_id": session_id,
                        "fraud_analysis_available": False,
                        "message": "No fraud analysis has been performed for this session"
                    }
                
                return {
                    "session_id": session_id,
                    "fraud_analysis_available": True,
                    "overall_fraud_score": float(fraud_indicator.overall_fraud_score) if fraud_indicator.overall_fraud_score else None,
                    "is_duplicate": fraud_indicator.is_duplicate,
                    "fraud_confidence": float(fraud_indicator.fraud_confidence) if fraud_indicator.fraud_confidence else None,
                    "risk_level": fraud_indicator.risk_level,
                    "ip_analysis": {
                        "ip_address": fraud_indicator.ip_address,
                        "usage_count": fraud_indicator.ip_usage_count,
                        "sessions_today": fraud_indicator.ip_sessions_today,
                        "risk_score": float(fraud_indicator.ip_risk_score) if fraud_indicator.ip_risk_score else None,
                        "country_code": fraud_indicator.ip_country_code
                    },
                    "device_fingerprint": {
                        "fingerprint": fraud_indicator.device_fingerprint,
                        "usage_count": fraud_indicator.fingerprint_usage_count,
                        "risk_score": float(fraud_indicator.fingerprint_risk_score) if fraud_indicator.fingerprint_risk_score else None
                    },
                    "duplicate_responses": {
                        "similarity_score": float(fraud_indicator.response_similarity_score) if fraud_indicator.response_similarity_score else None,
                        "duplicate_count": fraud_indicator.duplicate_response_count,
                        "risk_score": float(fraud_indicator.response_similarity_score) if fraud_indicator.response_similarity_score else None
                    },
                    "geolocation": {
                        "consistent": fraud_indicator.geolocation_consistent,
                        "risk_score": float(fraud_indicator.geolocation_risk_score) if fraud_indicator.geolocation_risk_score else None,
                        "country_code": fraud_indicator.ip_country_code
                    },
                    "velocity": {
                        "responses_per_hour": float(fraud_indicator.responses_per_hour) if fraud_indicator.responses_per_hour else None,
                        "risk_score": float(fraud_indicator.velocity_risk_score) if fraud_indicator.velocity_risk_score else None
                    },
                    "flag_reasons": fraud_indicator.flag_reasons,
                    "analysis_details": fraud_indicator.analysis_details,
                    "created_at": fraud_indicator.created_at.isoformat()
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting fraud indicators: {e}")
                raise HTTPException(status_code=500, detail="Failed to get fraud indicators")
        
        @self.router.get("/ip/{ip_address}")
        async def get_sessions_by_ip(
            ip_address: str,
            db: AsyncSession = Depends(get_db)
        ):
            """Get all sessions for a specific IP address."""
            try:
                # Get sessions with this IP
                sessions_query = select(Session).where(Session.ip_address == ip_address)
                sessions_result = await db.execute(sessions_query)
                sessions = sessions_result.scalars().all()
                
                return {
                    "ip_address": ip_address,
                    "session_count": len(sessions),
                    "sessions": [
                        {
                            "session_id": session.id,
                            "survey_id": session.survey_id,
                            "respondent_id": session.respondent_id,
                            "platform_id": session.platform_id,
                            "created_at": session.created_at.isoformat(),
                            "is_active": session.is_active
                        }
                        for session in sessions
                    ]
                }
                
            except Exception as e:
                logger.error(f"Error getting sessions by IP: {e}")
                raise HTTPException(status_code=500, detail="Failed to get sessions by IP")
        
        @self.router.get("/fingerprint/{fingerprint}")
        async def get_sessions_by_fingerprint(
            fingerprint: str,
            db: AsyncSession = Depends(get_db)
        ):
            """Get all sessions with a specific device fingerprint."""
            try:
                # Get sessions with this fingerprint
                sessions_query = select(Session).where(Session.device_fingerprint == fingerprint)
                sessions_result = await db.execute(sessions_query)
                sessions = sessions_result.scalars().all()
                
                return {
                    "device_fingerprint": fingerprint,
                    "session_count": len(sessions),
                    "sessions": [
                        {
                            "session_id": session.id,
                            "survey_id": session.survey_id,
                            "respondent_id": session.respondent_id,
                            "platform_id": session.platform_id,
                            "ip_address": session.ip_address,
                            "created_at": session.created_at.isoformat(),
                            "is_active": session.is_active
                        }
                        for session in sessions
                    ]
                }
                
            except Exception as e:
                logger.error(f"Error getting sessions by fingerprint: {e}")
                raise HTTPException(status_code=500, detail="Failed to get sessions by fingerprint")
        
        @self.router.get("/dashboard/summary")
        async def get_fraud_dashboard_summary(
            survey_id: Optional[str] = None,
            days: int = 7,
            db: AsyncSession = Depends(get_db)
        ):
            """Get aggregate fraud statistics for dashboard."""
            try:
                # Calculate date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # Build query
                query = select(FraudIndicator).where(
                    FraudIndicator.created_at >= start_date
                )
                
                if survey_id:
                    # Join with sessions to filter by survey_id
                    query = query.join(Session, FraudIndicator.session_id == Session.id).where(
                        Session.survey_id == survey_id
                    )
                
                result = await db.execute(query)
                fraud_indicators = result.scalars().all()
                
                # Calculate statistics
                total_sessions = len(fraud_indicators)
                duplicate_count = sum(1 for fi in fraud_indicators if fi.is_duplicate)
                high_risk_count = sum(1 for fi in fraud_indicators if fi.overall_fraud_score and float(fi.overall_fraud_score) >= 0.7)
                
                # Average fraud score
                fraud_scores = [float(fi.overall_fraud_score) for fi in fraud_indicators if fi.overall_fraud_score]
                avg_fraud_score = sum(fraud_scores) / len(fraud_scores) if fraud_scores else 0.0
                
                # Top suspicious IPs
                ip_counts = {}
                for fi in fraud_indicators:
                    if fi.ip_address:
                        if fi.ip_address not in ip_counts:
                            ip_counts[fi.ip_address] = {"count": 0, "risk_score": 0.0}
                        ip_counts[fi.ip_address]["count"] += 1
                        if fi.ip_risk_score:
                            ip_counts[fi.ip_address]["risk_score"] = max(
                                ip_counts[fi.ip_address]["risk_score"],
                                float(fi.ip_risk_score)
                            )
                
                top_ips = sorted(
                    [{"ip": ip, **data} for ip, data in ip_counts.items()],
                    key=lambda x: x["count"],
                    reverse=True
                )[:10]
                
                return {
                    "period_days": days,
                    "survey_id": survey_id,
                    "total_sessions_analyzed": total_sessions,
                    "duplicate_sessions": duplicate_count,
                    "high_risk_sessions": high_risk_count,
                    "average_fraud_score": avg_fraud_score,
                    "duplicate_rate": (duplicate_count / total_sessions * 100) if total_sessions > 0 else 0.0,
                    "high_risk_rate": (high_risk_count / total_sessions * 100) if total_sessions > 0 else 0.0,
                    "top_suspicious_ips": top_ips
                }
                
            except Exception as e:
                logger.error(f"Error getting fraud dashboard summary: {e}")
                raise HTTPException(status_code=500, detail="Failed to get fraud dashboard summary")
        
        @self.router.get("/dashboard/duplicates")
        async def get_duplicate_sessions(
            survey_id: Optional[str] = None,
            limit: int = 50,
            db: AsyncSession = Depends(get_db)
        ):
            """List potential duplicate sessions."""
            try:
                # Build query for duplicate sessions
                query = select(FraudIndicator).where(
                    FraudIndicator.is_duplicate == True
                )
                
                if survey_id:
                    query = query.join(Session, FraudIndicator.session_id == Session.id).where(
                        Session.survey_id == survey_id
                    )
                
                query = query.order_by(FraudIndicator.created_at.desc()).limit(limit)
                
                result = await db.execute(query)
                fraud_indicators = result.scalars().all()
                
                # Get session details
                duplicate_sessions = []
                for fi in fraud_indicators:
                    session_query = select(Session).where(Session.id == fi.session_id)
                    session_result = await db.execute(session_query)
                    session = session_result.scalar_one_or_none()
                    
                    if session:
                        duplicate_sessions.append({
                            "session_id": session.id,
                            "survey_id": session.survey_id,
                            "respondent_id": session.respondent_id,
                            "platform_id": session.platform_id,
                            "ip_address": session.ip_address,
                            "device_fingerprint": session.device_fingerprint,
                            "fraud_score": float(fi.overall_fraud_score) if fi.overall_fraud_score else None,
                            "flag_reasons": fi.flag_reasons,
                            "created_at": session.created_at.isoformat()
                        })
                
                return {
                    "duplicate_count": len(duplicate_sessions),
                    "sessions": duplicate_sessions
                }
                
            except Exception as e:
                logger.error(f"Error getting duplicate sessions: {e}")
                raise HTTPException(status_code=500, detail="Failed to get duplicate sessions")
        
        @self.router.post("/analyze/{session_id}")
        async def analyze_session_fraud(
            session_id: str,
            db: AsyncSession = Depends(get_db)
        ):
            """Trigger fraud analysis for a session."""
            try:
                # Validate session exists
                session_query = select(Session).where(Session.id == session_id)
                session_result = await db.execute(session_query)
                session = session_result.scalar_one_or_none()
                
                if not session:
                    raise HTTPException(status_code=404, detail="Session not found")
                
                # Get behavior data
                behavior_query = select(BehaviorData).where(BehaviorData.session_id == session_id)
                behavior_result = await db.execute(behavior_query)
                behavior_data = behavior_result.scalars().all()
                
                # Perform fraud analysis
                fraud_indicator = await self.fraud_service.analyze_session_fraud(
                    session, behavior_data, db
                )
                
                # Save fraud indicator
                db.add(fraud_indicator)
                await db.commit()
                await db.refresh(fraud_indicator)
                
                logger.info(f"Fraud analysis completed for session {session_id}")
                
                return {
                    "session_id": session_id,
                    "overall_fraud_score": float(fraud_indicator.overall_fraud_score) if fraud_indicator.overall_fraud_score else None,
                    "is_duplicate": fraud_indicator.is_duplicate,
                    "risk_level": fraud_indicator.risk_level,
                    "flag_reasons": fraud_indicator.flag_reasons,
                    "created_at": fraud_indicator.created_at.isoformat()
                }
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error analyzing session fraud: {e}")
                await db.rollback()
                raise HTTPException(status_code=500, detail="Failed to analyze session fraud")
    
    def get_router(self) -> APIRouter:
        """Get the router for this controller."""
        return self.router
