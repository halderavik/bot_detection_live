"""
Test suite for text analysis dashboard endpoints.

This module tests the new dashboard endpoints that provide aggregated
text quality statistics and respondent-level analysis.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from app.database import get_db
from app.models import Session, SurveyQuestion, SurveyResponse


class TestTextAnalysisDashboardEndpoints:
    """Test class for text analysis dashboard API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def sample_sessions(self):
        """Create sample session data for testing."""
        now = datetime.utcnow()
        return [
            Session(
                id="session-1",
                survey_id="survey-1",
                respondent_id="respondent-1",
                created_at=now - timedelta(days=1),
                is_active=True,
                platform="test"
            ),
            Session(
                id="session-2", 
                survey_id="survey-1",
                respondent_id="respondent-2",
                created_at=now - timedelta(days=2),
                is_active=True,
                platform="test"
            ),
            Session(
                id="session-3",
                survey_id="survey-2", 
                respondent_id="respondent-3",
                created_at=now - timedelta(days=3),
                is_active=True,
                platform="test"
            )
        ]

    @pytest.fixture
    def sample_survey_responses(self, sample_sessions):
        """Create sample survey response data for testing."""
        now = datetime.utcnow()
        return [
            # Session 1 - High quality responses
            SurveyResponse(
                id="response-1",
                question_id="question-1",
                session_id="session-1",
                response_text="This is a detailed and thoughtful response about the topic.",
                quality_score=85.0,
                is_flagged=False,
                flag_reasons={},
                analyzed_at=now - timedelta(hours=1)
            ),
            SurveyResponse(
                id="response-2",
                question_id="question-2", 
                session_id="session-1",
                response_text="Another high-quality response with good insights.",
                quality_score=78.0,
                is_flagged=False,
                flag_reasons={},
                analyzed_at=now - timedelta(hours=2)
            ),
            # Session 2 - Mixed quality responses
            SurveyResponse(
                id="response-3",
                question_id="question-1",
                session_id="session-2", 
                response_text="Good response with valid content.",
                quality_score=72.0,
                is_flagged=False,
                flag_reasons={},
                analyzed_at=now - timedelta(hours=3)
            ),
            SurveyResponse(
                id="response-4",
                question_id="question-2",
                session_id="session-2",
                response_text="asdfghjkl random gibberish text",
                quality_score=15.0,
                is_flagged=True,
                flag_reasons={"gibberish": {"score": 0.8, "reason": "Contains random characters"}},
                analyzed_at=now - timedelta(hours=4)
            ),
            # Session 3 - Low quality responses
            SurveyResponse(
                id="response-5",
                question_id="question-1",
                session_id="session-3",
                response_text="Not relevant to the question at all.",
                quality_score=25.0,
                is_flagged=True,
                flag_reasons={"relevance": {"score": 0.9, "reason": "Not relevant to question"}},
                analyzed_at=now - timedelta(hours=5)
            ),
            SurveyResponse(
                id="response-6",
                question_id="question-2",
                session_id="session-3",
                response_text="I don't know",
                quality_score=40.0,
                is_flagged=True,
                flag_reasons={"generic": {"score": 0.7, "reason": "Generic response"}},
                analyzed_at=now - timedelta(hours=6)
            )
        ]

    @pytest.mark.asyncio
    async def test_dashboard_summary_empty_data(self, mock_db_session):
        """Test dashboard summary with no data returns zeros."""
        from app.controllers.text_analysis_controller import get_dashboard_summary
        
        # Mock empty query result - fix async mock setup
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result
        
        result = await get_dashboard_summary(
            days=7,
            survey_id=None,
            db=mock_db_session
        )
        
        assert result["total_responses"] == 0
        assert result["avg_quality_score"] is None
        assert result["flagged_count"] == 0
        assert result["flagged_percentage"] == 0.0
        assert result["quality_distribution"] == {}

    @pytest.mark.asyncio
    async def test_dashboard_summary_with_data(self, mock_db_session, sample_survey_responses):
        """Test dashboard summary with sample data."""
        from app.controllers.text_analysis_controller import get_dashboard_summary
        
        # Mock query result - fix async mock setup
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = sample_survey_responses
        mock_db_session.execute.return_value = mock_result
        
        result = await get_dashboard_summary(
            days=30,
            survey_id=None,
            db=mock_db_session
        )
        
        # Verify totals
        assert result["total_responses"] == 6
        assert result["flagged_count"] == 3
        assert result["flagged_percentage"] == 50.0
        
        # Verify average quality score (85+78+72+15+25+40)/6 = 52.5
        assert result["avg_quality_score"] == 52.5
        
        # Verify quality distribution buckets (0-10, 10-20, ..., 90-100)
        quality_dist = result["quality_distribution"]
        assert "0-10" in quality_dist
        assert "10-20" in quality_dist
        assert "70-80" in quality_dist
        assert "80-90" in quality_dist
        
        # Verify specific bucket counts
        assert quality_dist["80-90"] == 1  # score 85
        assert quality_dist["70-80"] == 2  # scores 78, 72
        assert quality_dist["10-20"] == 1  # score 15
        assert quality_dist["20-30"] == 1  # score 25
        assert quality_dist["40-50"] == 1  # score 40

    @pytest.mark.asyncio
    async def test_dashboard_summary_survey_filter(self, mock_db_session, sample_survey_responses):
        """Test dashboard summary with survey filtering."""
        from app.controllers.text_analysis_controller import get_dashboard_summary
        
        # Filter responses for survey-1 only
        survey1_responses = [r for r in sample_survey_responses if r.session_id in ["session-1", "session-2"]]
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = survey1_responses
        
        result = await get_dashboard_summary(
            days=30,
            survey_id="survey-1",
            db=mock_db_session
        )
        
        assert result["total_responses"] == 4
        assert result["flagged_count"] == 1  # Only response-4 is flagged
        assert result["flagged_percentage"] == 25.0

    @pytest.mark.asyncio
    async def test_dashboard_summary_date_filtering(self, mock_db_session, sample_survey_responses):
        """Test dashboard summary with date range filtering."""
        from app.controllers.text_analysis_controller import get_dashboard_summary
        
        # Mock recent responses only (last 1 day)
        recent_responses = sample_survey_responses[:2]  # responses 1 and 2
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = recent_responses
        
        result = await get_dashboard_summary(
            days=1,
            survey_id=None,
            db=mock_db_session
        )
        
        assert result["total_responses"] == 2
        assert result["flagged_count"] == 0  # Both recent responses are high quality
        assert result["flagged_percentage"] == 0.0
        assert result["avg_quality_score"] == 81.5  # (85+78)/2

    @pytest.mark.asyncio
    async def test_respondent_analysis_pagination(self, mock_db_session, sample_sessions):
        """Test respondent analysis with pagination."""
        from app.controllers.text_analysis_controller import get_respondent_analysis
        
        # Mock session query result
        mock_sessions_with_counts = [
            (sample_sessions[0], 2),  # session-1 has 2 responses
            (sample_sessions[1], 2),  # session-2 has 2 responses
            (sample_sessions[2], 2),  # session-3 has 2 responses
        ]
        
        # Mock first page (limit=2)
        mock_db_session.execute.return_value.all.return_value = mock_sessions_with_counts[:2]
        mock_db_session.execute.return_value.scalar.return_value = 3  # total count
        
        result = await get_respondent_analysis(
            survey_id=None,
            days=30,
            page=1,
            limit=2,
            db=mock_db_session
        )
        
        assert len(result["respondents"]) == 2
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["limit"] == 2
        assert result["pagination"]["total"] == 3
        assert result["pagination"]["pages"] == 2

    @pytest.mark.asyncio
    async def test_respondent_analysis_with_responses(self, mock_db_session, sample_sessions, sample_survey_responses):
        """Test respondent analysis with response data."""
        from app.controllers.text_analysis_controller import get_respondent_analysis
        
        # Mock session query
        mock_sessions_with_counts = [(sample_sessions[0], 2)]
        mock_db_session.execute.return_value.all.return_value = mock_sessions_with_counts
        mock_db_session.execute.return_value.scalar.return_value = 1
        
        # Mock responses for session-1
        session1_responses = [r for r in sample_survey_responses if r.session_id == "session-1"]
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = session1_responses
        
        result = await get_respondent_analysis(
            survey_id=None,
            days=30,
            page=1,
            limit=50,
            db=mock_db_session
        )
        
        respondent = result["respondents"][0]
        assert respondent["respondent_id"] == "respondent-1"
        assert respondent["session_id"] == "session-1"
        assert respondent["survey_id"] == "survey-1"
        assert respondent["response_count"] == 2
        assert respondent["flagged_count"] == 0
        assert respondent["flagged_percentage"] == 0.0
        assert respondent["avg_quality_score"] == 81.5  # (85+78)/2

    @pytest.mark.asyncio
    async def test_respondent_analysis_survey_filter(self, mock_db_session, sample_sessions):
        """Test respondent analysis with survey filtering."""
        from app.controllers.text_analysis_controller import get_respondent_analysis
        
        # Filter sessions for survey-1 only
        survey1_sessions = [s for s in sample_sessions if s.survey_id == "survey-1"]
        mock_sessions_with_counts = [(s, 0) for s in survey1_sessions]
        
        mock_db_session.execute.return_value.all.return_value = mock_sessions_with_counts
        mock_db_session.execute.return_value.scalar.return_value = 2
        
        result = await get_respondent_analysis(
            survey_id="survey-1",
            days=30,
            page=1,
            limit=50,
            db=mock_db_session
        )
        
        assert len(result["respondents"]) == 2
        assert all(r["survey_id"] == "survey-1" for r in result["respondents"])

    @pytest.mark.asyncio
    async def test_respondent_analysis_no_responses(self, mock_db_session, sample_sessions):
        """Test respondent analysis for sessions with no text responses."""
        from app.controllers.text_analysis_controller import get_respondent_analysis
        
        # Mock session with 0 responses
        mock_sessions_with_counts = [(sample_sessions[0], 0)]
        mock_db_session.execute.return_value.all.return_value = mock_sessions_with_counts
        mock_db_session.execute.return_value.scalar.return_value = 1
        
        result = await get_respondent_analysis(
            survey_id=None,
            days=30,
            page=1,
            limit=50,
            db=mock_db_session
        )
        
        respondent = result["respondents"][0]
        assert respondent["response_count"] == 0
        assert respondent["avg_quality_score"] is None
        assert respondent["flagged_count"] == 0
        assert respondent["flagged_percentage"] == 0.0
        assert respondent["quality_scores"] == []
        assert respondent["flag_reasons_summary"] == {}

    @pytest.mark.asyncio
    async def test_respondent_analysis_flag_reasons_aggregation(self, mock_db_session, sample_sessions, sample_survey_responses):
        """Test flag reasons aggregation across responses."""
        from app.controllers.text_analysis_controller import get_respondent_analysis
        
        # Mock session with flagged responses
        mock_sessions_with_counts = [(sample_sessions[2], 2)]  # session-3 has flagged responses
        mock_db_session.execute.return_value.all.return_value = mock_sessions_with_counts
        mock_db_session.execute.return_value.scalar.return_value = 1
        
        # Mock responses for session-3 (both flagged)
        session3_responses = [r for r in sample_survey_responses if r.session_id == "session-3"]
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = session3_responses
        
        result = await get_respondent_analysis(
            survey_id=None,
            days=30,
            page=1,
            limit=50,
            db=mock_db_session
        )
        
        respondent = result["respondents"][0]
        assert respondent["flagged_count"] == 2
        assert respondent["flagged_percentage"] == 100.0
        
        # Check flag reasons aggregation
        flag_reasons = respondent["flag_reasons_summary"]
        assert "relevance" in flag_reasons
        assert "generic" in flag_reasons
        assert flag_reasons["relevance"] == 1
        assert flag_reasons["generic"] == 1

    @pytest.mark.asyncio
    async def test_dashboard_summary_quality_distribution_buckets(self, mock_db_session):
        """Test that quality distribution has exactly 10 buckets."""
        from app.controllers.text_analysis_controller import get_dashboard_summary
        
        # Create responses with scores in different buckets
        responses = []
        for i in range(10):
            score = i * 10 + 5  # 5, 15, 25, ..., 95
            responses.append(
                SurveyResponse(
                    id=f"response-{i}",
                    question_id="question-1",
                    session_id="session-1",
                    response_text=f"Response {i}",
                    quality_score=score,
                    is_flagged=score < 50,
                    flag_reasons={} if score >= 50 else {"low_quality": {}},
                    analyzed_at=datetime.utcnow()
                )
            )
        
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = responses
        
        result = await get_dashboard_summary(
            days=30,
            survey_id=None,
            db=mock_db_session
        )
        
        quality_dist = result["quality_distribution"]
        assert len(quality_dist) == 10
        
        # Verify bucket names
        expected_buckets = [
            "0-10", "10-20", "20-30", "30-40", "40-50",
            "50-60", "60-70", "70-80", "80-90", "90-100"
        ]
        for bucket in expected_buckets:
            assert bucket in quality_dist

    @pytest.mark.asyncio
    async def test_dashboard_summary_error_handling(self, mock_db_session):
        """Test dashboard summary error handling."""
        from app.controllers.text_analysis_controller import get_dashboard_summary
        from fastapi import HTTPException
        
        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_dashboard_summary(
                days=30,
                survey_id=None,
                db=mock_db_session
            )
        
        assert exc_info.value.status_code == 500
        assert "Failed to get dashboard summary" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_respondent_analysis_error_handling(self, mock_db_session):
        """Test respondent analysis error handling."""
        from app.controllers.text_analysis_controller import get_respondent_analysis
        from fastapi import HTTPException
        
        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_respondent_analysis(
                survey_id=None,
                days=30,
                page=1,
                limit=50,
                db=mock_db_session
            )
        
        assert exc_info.value.status_code == 500
        assert "Failed to get respondent analysis" in str(exc_info.value.detail)
