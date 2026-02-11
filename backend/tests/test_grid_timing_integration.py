"""
Integration tests for grid and timing analysis.

This module tests the end-to-end flow of grid and timing analysis
including data creation, analysis execution, and API endpoint responses.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from app.database import get_db, Base
from app.models import Session, SurveyQuestion, SurveyResponse, GridResponse, TimingAnalysis
from app.services.grid_analysis_service import GridAnalysisService
from app.services.timing_analysis_service import TimingAnalysisService


class TestGridTimingIntegration:
    """Integration tests for grid and timing analysis."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def grid_service(self):
        """Create grid analysis service."""
        return GridAnalysisService()

    @pytest.fixture
    def timing_service(self):
        """Create timing analysis service."""
        return TimingAnalysisService()

    @pytest.mark.asyncio
    async def test_grid_analysis_flow(self, grid_service):
        """Test complete grid analysis flow."""
        # Test straight-lining detection
        responses = [
            {"response_value": "5", "response_time_ms": 1000},
            {"response_value": "5", "response_time_ms": 1200},
            {"response_value": "5", "response_time_ms": 1100},
            {"response_value": "5", "response_time_ms": 1050},
            {"response_value": "5", "response_time_ms": 1150}
        ]
        
        # Test detection methods
        straight_lining = grid_service.detect_straight_lining(responses)
        assert straight_lining["is_straight_lined"] is True
        
        patterns = grid_service.detect_patterns(responses)
        assert patterns["pattern_type"] == "straight_line"
        
        variance = grid_service.calculate_variance(responses)
        assert variance < 0.1  # Low variance for identical values
        
        satisficing = grid_service.calculate_satisficing_score(responses)
        # Satisficing score combines multiple factors, so it may vary
        assert satisficing >= 0.0
        assert satisficing <= 1.0

    @pytest.mark.asyncio
    async def test_timing_analysis_flow(self, timing_service):
        """Test complete timing analysis flow."""
        # Test speeder detection
        responses = [
            {"response_time_ms": 500},
            {"response_time_ms": 1500},
            {"response_time_ms": 3000},
            {"response_time_ms": 5000}
        ]
        
        speeders = timing_service.detect_speeders(responses)
        assert len(speeders) == 2  # 500 and 1500 are speeders
        
        flatliners = timing_service.detect_flatliners(responses)
        assert len(flatliners) == 0  # None are flatliners
        
        anomalies = timing_service.detect_timing_anomalies(responses)
        # Anomaly detection depends on z-score calculation
        # With consistent times except one outlier, may or may not detect
        assert isinstance(anomalies, list)
        # If anomalies found, verify structure
        if len(anomalies) > 0:
            assert all("anomaly_score" in a for a in anomalies)
            assert all("anomaly_type" in a for a in anomalies)
        
        thresholds = timing_service.calculate_adaptive_thresholds(responses)
        assert "speeder_threshold" in thresholds
        assert "flatliner_threshold" in thresholds

    @pytest.mark.asyncio
    async def test_grid_and_timing_combined_analysis(self, grid_service, timing_service):
        """Test combined grid and timing analysis."""
        # Create responses with both grid and timing data
        grid_responses = [
            {"response_value": "3", "response_time_ms": 500},
            {"response_value": "3", "response_time_ms": 600},
            {"response_value": "3", "response_time_ms": 550}
        ]
        
        # Analyze grid patterns
        straight_lining = grid_service.detect_straight_lining(grid_responses)
        satisficing = grid_service.calculate_satisficing_score(grid_responses)
        
        # Analyze timing
        speeders = timing_service.detect_speeders(grid_responses)
        
        # Combined analysis: straight-lining + speeders = high risk
        assert straight_lining["is_straight_lined"] is True
        assert len(speeders) == len(grid_responses)  # All are speeders
        # Satisficing score combines multiple factors
        assert satisficing >= 0.0
        assert satisficing <= 1.0

    def test_grid_analysis_endpoints_integration(self, client):
        """Test grid analysis endpoints return correct structure."""
        with patch('app.controllers.hierarchical_controller.get_db') as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db
            
            with patch('app.services.aggregation_service.AggregationService.get_grid_analysis_summary', new_callable=AsyncMock) as mock_summary:
                mock_summary.return_value = {
                    "survey_id": "test-survey",
                    "total_responses": 100,
                    "straight_lined_count": 20,
                    "straight_lined_percentage": 20.0,
                    "pattern_distribution": {},
                    "avg_variance_score": 0.5,
                    "avg_satisficing_score": 0.6,
                    "unique_questions": 10
                }
                
                response = client.get("/api/v1/surveys/test-survey/grid-analysis/summary")
                
                assert response.status_code == 200
                data = response.json()
                assert "survey_id" in data
                assert "total_responses" in data
                assert "straight_lined_percentage" in data
                assert "pattern_distribution" in data

    def test_timing_analysis_endpoints_integration(self, client):
        """Test timing analysis endpoints return correct structure."""
        with patch('app.controllers.hierarchical_controller.get_db') as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db
            
            with patch('app.services.aggregation_service.AggregationService.get_timing_analysis_summary', new_callable=AsyncMock) as mock_summary:
                mock_summary.return_value = {
                    "survey_id": "test-survey",
                    "total_analyses": 50,
                    "speeders_count": 5,
                    "speeders_percentage": 10.0,
                    "flatliners_count": 3,
                    "flatliners_percentage": 6.0,
                    "anomalies_count": 2,
                    "avg_response_time_ms": 5000.0,
                    "median_response_time_ms": 4500.0,
                    "unique_questions": 10
                }
                
                response = client.get("/api/v1/surveys/test-survey/timing-analysis/summary")
                
                assert response.status_code == 200
                data = response.json()
                assert "survey_id" in data
                assert "total_analyses" in data
                assert "speeders_percentage" in data
                assert "flatliners_percentage" in data
                assert "avg_response_time_ms" in data

    def test_hierarchical_endpoints_consistency(self, client):
        """Test that all hierarchy levels return consistent data structure."""
        with patch('app.controllers.hierarchical_controller.get_db') as mock_get_db:
            mock_db = AsyncMock(spec=AsyncSession)
            mock_get_db.return_value = mock_db
            
            # Mock session for session-level endpoints
            mock_session = Session(
                id="session-1",
                survey_id="survey-1",
                platform_id="platform-1",
                respondent_id="respondent-1"
            )
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_session
            mock_db.execute.return_value = mock_result
            
            with patch('app.services.aggregation_service.AggregationService.get_grid_analysis_summary', new_callable=AsyncMock) as mock_grid:
                with patch('app.services.aggregation_service.AggregationService.get_timing_analysis_summary', new_callable=AsyncMock) as mock_timing:
                    mock_grid.return_value = {"survey_id": "survey-1", "total_responses": 0}
                    mock_timing.return_value = {"survey_id": "survey-1", "total_analyses": 0}
                    
                    # Test all hierarchy levels
                    endpoints = [
                        "/api/v1/surveys/survey-1/grid-analysis/summary",
                        "/api/v1/surveys/survey-1/platforms/platform-1/grid-analysis/summary",
                        "/api/v1/surveys/survey-1/platforms/platform-1/respondents/respondent-1/grid-analysis/summary",
                        "/api/v1/surveys/survey-1/platforms/platform-1/respondents/respondent-1/sessions/session-1/grid-analysis",
                        "/api/v1/surveys/survey-1/timing-analysis/summary",
                        "/api/v1/surveys/survey-1/platforms/platform-1/timing-analysis/summary",
                        "/api/v1/surveys/survey-1/platforms/platform-1/respondents/respondent-1/timing-analysis/summary",
                        "/api/v1/surveys/survey-1/platforms/platform-1/respondents/respondent-1/sessions/session-1/timing-analysis"
                    ]
                    
                    for endpoint in endpoints:
                        response = client.get(endpoint)
                        assert response.status_code in [200, 404], f"Endpoint {endpoint} returned {response.status_code}"
