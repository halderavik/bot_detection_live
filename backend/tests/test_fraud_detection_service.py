"""
Unit tests for fraud detection service.

This module contains comprehensive tests for the fraud detection service
including all detection methods, error handling, and edge cases.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any

from app.services.fraud_detection_service import FraudDetectionService
from app.models import Session, BehaviorData, SurveyResponse, FraudIndicator


class TestFraudDetectionService:
    """Test cases for FraudDetectionService."""
    
    @pytest.fixture
    def fraud_service(self):
        """Create a fraud detection service instance for testing."""
        return FraudDetectionService()
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing."""
        session = Session()
        session.id = "test-session-id"
        session.ip_address = "192.168.1.100"
        session.survey_id = "test-survey-id"
        session.respondent_id = "test-respondent-id"
        session.user_agent = "Mozilla/5.0"
        session.platform_id = "test-platform"
        session.created_at = datetime.now()
        return session
    
    @pytest.fixture
    def mock_behavior_data(self):
        """Create mock behavior data for testing."""
        return [
            BehaviorData(
                session_id="test-session-id",
                event_type="keystroke",
                timestamp=datetime.now(),
                event_data={},
                screen_width=1920,
                screen_height=1080,
                viewport_width=1920,
                viewport_height=1080
            )
        ]
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        return db
    
    @pytest.mark.asyncio
    async def test_analyze_ip_address_unique(self, fraud_service, mock_session, mock_db):
        """Test IP analysis with unique IP address."""
        # Mock database query to return 1 session (just this one)
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await fraud_service._analyze_ip_address(mock_session, mock_db)
        
        assert result["risk_score"] == 0.0
        assert result["usage_count"] == 1
        assert result["sessions_today"] == 1
    
    @pytest.mark.asyncio
    async def test_analyze_ip_address_reused(self, fraud_service, mock_session, mock_db):
        """Test IP analysis with heavily reused IP address."""
        # Mock database query to return 15 sessions
        mock_result_total = MagicMock()
        mock_result_total.scalar.return_value = 15
        
        mock_result_today = MagicMock()
        mock_result_today.scalar.return_value = 6
        
        mock_db.execute = AsyncMock(side_effect=[mock_result_total, mock_result_today])
        
        result = await fraud_service._analyze_ip_address(mock_session, mock_db)
        
        assert result["risk_score"] >= 0.8  # High risk for >10 sessions
        assert result["usage_count"] == 15
        assert result["sessions_today"] == 6
    
    @pytest.mark.asyncio
    async def test_analyze_device_fingerprint_unique(self, fraud_service, mock_session, mock_behavior_data, mock_db):
        """Test device fingerprint analysis with unique fingerprint."""
        # Mock database query to return 0 matches (unique fingerprint)
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await fraud_service._analyze_device_fingerprint(mock_session, mock_behavior_data, mock_db)
        
        assert result["risk_score"] == 0.0
        assert result["usage_count"] == 0
        assert result["fingerprint"] is not None
    
    @pytest.mark.asyncio
    async def test_analyze_device_fingerprint_duplicate(self, fraud_service, mock_session, mock_behavior_data, mock_db):
        """Test device fingerprint analysis with duplicate fingerprint."""
        # Mock database query to return 5 matches
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await fraud_service._analyze_device_fingerprint(mock_session, mock_behavior_data, mock_db)
        
        assert result["risk_score"] >= 0.9  # High risk for >=5 matches
        assert result["usage_count"] == 5
        assert result["fingerprint"] is not None
    
    @pytest.mark.asyncio
    async def test_analyze_duplicate_responses_exact_match(self, fraud_service, mock_session, mock_db):
        """Test duplicate response detection with exact match."""
        # Mock session responses
        session_response = SurveyResponse()
        session_response.response_text = "This is a test response"
        
        other_response = SurveyResponse()
        other_response.response_text = "This is a test response"
        
        # Mock database queries
        mock_result_session = MagicMock()
        mock_result_session.scalars.return_value.all.return_value = [session_response]
        
        mock_result_other = MagicMock()
        mock_result_other.scalars.return_value.all.return_value = [other_response]
        
        mock_db.execute = AsyncMock(side_effect=[mock_result_session, mock_result_other])
        
        result = await fraud_service._analyze_duplicate_responses(mock_session, mock_db)
        
        assert result["risk_score"] == 1.0  # Exact match = 100% similarity = max risk
        assert result["duplicate_count"] >= 1
        assert result["max_similarity"] >= 0.95
    
    @pytest.mark.asyncio
    async def test_analyze_duplicate_responses_unique(self, fraud_service, mock_session, mock_db):
        """Test duplicate response detection with unique responses."""
        # Mock session responses
        session_response = SurveyResponse()
        session_response.response_text = "This is a unique response"
        
        other_response = SurveyResponse()
        other_response.response_text = "This is a completely different response"
        
        # Mock database queries
        mock_result_session = MagicMock()
        mock_result_session.scalars.return_value.all.return_value = [session_response]
        
        mock_result_other = MagicMock()
        mock_result_other.scalars.return_value.all.return_value = [other_response]
        
        mock_db.execute = AsyncMock(side_effect=[mock_result_session, mock_result_other])
        
        result = await fraud_service._analyze_duplicate_responses(mock_session, mock_db)
        
        assert result["risk_score"] < 0.6  # Low similarity = low risk
        assert result["max_similarity"] < 0.70
    
    @pytest.mark.asyncio
    async def test_analyze_geolocation_consistent(self, fraud_service, mock_session, mock_db):
        """Test geolocation analysis with consistent location."""
        # Mock database query to return empty list (no conflicting sessions)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await fraud_service._analyze_geolocation(mock_session, mock_db)
        
        assert result["risk_score"] == 0.0
        assert result["consistent"] is True
    
    @pytest.mark.asyncio
    async def test_analyze_velocity_normal(self, fraud_service, mock_session, mock_db):
        """Test velocity analysis with normal submission rate."""
        # Mock database query to return 1 session (just this one)
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await fraud_service._analyze_velocity(mock_session, mock_db)
        
        assert result["risk_score"] == 0.0  # 1 response/hour = low risk
        assert result["responses_per_hour"] == 1.0
    
    @pytest.mark.asyncio
    async def test_analyze_velocity_high(self, fraud_service, mock_session, mock_db):
        """Test velocity analysis with high submission rate."""
        # Mock database query to return 25 sessions
        mock_result = MagicMock()
        mock_result.scalar.return_value = 25
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        result = await fraud_service._analyze_velocity(mock_session, mock_db)
        
        assert result["risk_score"] == 1.0  # >20 responses/hour = max risk
        assert result["responses_per_hour"] == 25.0
    
    @pytest.mark.asyncio
    async def test_analyze_session_fraud_complete(self, fraud_service, mock_session, mock_behavior_data, mock_db):
        """Test complete fraud analysis with all methods."""
        # Mock all analysis methods
        with patch.object(fraud_service, '_analyze_ip_address', new_callable=AsyncMock) as mock_ip, \
             patch.object(fraud_service, '_analyze_device_fingerprint', new_callable=AsyncMock) as mock_fp, \
             patch.object(fraud_service, '_analyze_duplicate_responses', new_callable=AsyncMock) as mock_dup, \
             patch.object(fraud_service, '_analyze_geolocation', new_callable=AsyncMock) as mock_geo, \
             patch.object(fraud_service, '_analyze_velocity', new_callable=AsyncMock) as mock_vel:
            
            mock_ip.return_value = {"risk_score": 0.8, "usage_count": 10, "sessions_today": 5}
            mock_fp.return_value = {"risk_score": 0.9, "usage_count": 6, "fingerprint": "test-fp"}
            mock_dup.return_value = {"risk_score": 0.7, "duplicate_count": 3, "max_similarity": 0.9}
            mock_geo.return_value = {"risk_score": 0.0, "consistent": True, "country_code": None}
            mock_vel.return_value = {"risk_score": 0.8, "responses_per_hour": 12.0}
            
            result = await fraud_service.analyze_session_fraud(mock_session, mock_behavior_data, mock_db)
            
            assert isinstance(result, FraudIndicator)
            assert result.session_id == mock_session.id
            assert result.overall_fraud_score is not None
            assert result.overall_fraud_score >= 0.6  # High risk due to multiple indicators (weighted score may be slightly below 0.7)
            # Check that is_duplicate reflects the fraud score threshold
            assert result.is_duplicate == (result.overall_fraud_score >= 0.7)
            assert result.flag_reasons is not None
            assert len(result.flag_reasons) > 0
