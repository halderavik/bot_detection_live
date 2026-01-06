"""
API tests for fraud detection endpoints.

This module contains tests for the fraud detection API endpoints
including fraud analysis, IP tracking, and duplicate detection.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime

from main import app

client = TestClient(app)


class TestFraudDetectionAPI:
    """Test cases for fraud detection API endpoints."""
    
    def test_fraud_endpoints_exist(self):
        """Test that fraud detection endpoints are accessible (not 404)."""
        # Test that endpoints exist and return proper error codes (not 404)
        # We'll use a dummy session ID to test endpoint existence
        response = client.get("/api/v1/fraud/sessions/test-session-id")
        assert response.status_code != 404, "Fraud detection endpoints should not return 404"
    
    def test_get_fraud_indicators_session_not_found(self):
        """Test getting fraud indicators for non-existent session."""
        response = client.get("/api/v1/fraud/sessions/non-existent-session-id")
        assert response.status_code == 404
    
    def test_get_sessions_by_ip(self):
        """Test getting sessions by IP address."""
        # This should work even if there are no sessions
        response = client.get("/api/v1/fraud/ip/192.168.1.100")
        assert response.status_code == 200
        assert "ip_address" in response.json()
        assert "session_count" in response.json()
        assert "sessions" in response.json()
    
    def test_get_sessions_by_fingerprint(self):
        """Test getting sessions by device fingerprint."""
        # This should work even if there are no sessions
        test_fingerprint = "test-fingerprint-hash-1234567890abcdef"
        response = client.get(f"/api/v1/fraud/fingerprint/{test_fingerprint}")
        assert response.status_code == 200
        assert "device_fingerprint" in response.json()
        assert "session_count" in response.json()
        assert "sessions" in response.json()
    
    def test_get_fraud_dashboard_summary(self):
        """Test getting fraud dashboard summary."""
        response = client.get("/api/v1/fraud/dashboard/summary?days=7")
        assert response.status_code == 200
        data = response.json()
        assert "total_sessions_analyzed" in data
        assert "duplicate_sessions" in data
        assert "high_risk_sessions" in data
        assert "average_fraud_score" in data
    
    def test_get_fraud_dashboard_summary_with_survey(self):
        """Test getting fraud dashboard summary filtered by survey."""
        response = client.get("/api/v1/fraud/dashboard/summary?days=7&survey_id=test-survey-id")
        assert response.status_code == 200
        data = response.json()
        assert "survey_id" in data
    
    def test_get_duplicate_sessions(self):
        """Test getting duplicate sessions list."""
        response = client.get("/api/v1/fraud/dashboard/duplicates?limit=50")
        assert response.status_code == 200
        data = response.json()
        assert "duplicate_count" in data
        assert "sessions" in data
    
    def test_get_duplicate_sessions_with_survey(self):
        """Test getting duplicate sessions filtered by survey."""
        response = client.get("/api/v1/fraud/dashboard/duplicates?limit=50&survey_id=test-survey-id")
        assert response.status_code == 200
    
    def test_analyze_session_fraud_not_found(self):
        """Test fraud analysis for non-existent session."""
        response = client.post("/api/v1/fraud/analyze/non-existent-session-id")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_analyze_session_fraud_flow(self):
        """Test complete fraud analysis flow."""
        # Create a session first
        session_response = client.post("/api/v1/detection/sessions", params={
            "survey_id": "test-survey",
            "platform_id": "test-platform",
            "respondent_id": "test-respondent"
        })
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]
        
        # Add some events to the session
        events = [
            {
                "event_type": "keystroke",
                "timestamp": datetime.now().isoformat(),
                "data": {"key": "a"}
            }
        ]
        events_response = client.post(
            f"/api/v1/detection/sessions/{session_id}/events",
            json=events
        )
        assert events_response.status_code == 200
        
        # Run fraud analysis
        fraud_response = client.post(f"/api/v1/fraud/analyze/{session_id}")
        assert fraud_response.status_code == 200
        fraud_data = fraud_response.json()
        assert "session_id" in fraud_data
        assert "overall_fraud_score" in fraud_data
        assert "is_duplicate" in fraud_data
        assert "risk_level" in fraud_data
        
        # Get fraud indicators
        indicators_response = client.get(f"/api/v1/fraud/sessions/{session_id}")
        assert indicators_response.status_code == 200
        indicators_data = indicators_response.json()
        assert "fraud_analysis_available" in indicators_data
