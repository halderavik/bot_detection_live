"""
End-to-end integration tests for text analysis dashboard.

This module tests the complete workflow from creating sessions and submitting
text responses to generating dashboard summaries and reports with text quality data.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json
import uuid

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from app.database import get_db, Base
from app.models import Session, SurveyQuestion, SurveyResponse, BehaviorData, DetectionResult
from app.services.text_analysis_service import TextAnalysisService
from app.services.report_service import ReportService
from app.controllers.text_analysis_controller import get_dashboard_summary, get_respondent_analysis


class TestTextAnalysisIntegration:
    """Test class for end-to-end text analysis integration."""

    @pytest.fixture
    async def test_db(self):
        """Create test database."""
        # Use in-memory SQLite for testing
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Create session factory
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        yield async_session
        
        # Cleanup
        await engine.dispose()

    @pytest.fixture
    def client(self, test_db):
        """Create test client with database override."""
        def override_get_db():
            return test_db
        
        app.dependency_overrides[get_db] = override_get_db
        yield TestClient(app)
        app.dependency_overrides.clear()

    @pytest.fixture
    async def sample_session_data(self, test_db):
        """Create sample session with survey responses for testing."""
        async with test_db() as db:
            # Create sessions
            sessions = []
            for i in range(3):
                session = Session(
                    id=f"session-{i+1}",
                    survey_id="test-survey-1",
                    respondent_id=f"respondent-{i+1}",
                    created_at=datetime.utcnow() - timedelta(days=i+1),
                    last_activity=datetime.utcnow() - timedelta(hours=i+1),
                    is_active=True,
                    platform="test"
                )
                db.add(session)
                sessions.append(session)
            
            # Create survey questions
            questions = []
            for i in range(2):
                question = SurveyQuestion(
                    id=f"question-{i+1}",
                    session_id="session-1",
                    question_text=f"What is your opinion on topic {i+1}?",
                    question_type="open_ended",
                    element_id=f"input-{i+1}",
                    page_url="https://test-survey.com/page1",
                    page_title="Test Survey Page"
                )
                db.add(question)
                questions.append(question)
            
            await db.commit()
            
            # Create survey responses with different quality scores
            responses = [
                # High quality responses for session-1
                SurveyResponse(
                    id="response-1",
                    question_id="question-1",
                    session_id="session-1",
                    response_text="This is a detailed and thoughtful response about the topic with good insights and analysis.",
                    quality_score=88.0,
                    is_flagged=False,
                    flag_reasons={},
                    gibberish_score=0.1,
                    copy_paste_score=0.1,
                    relevance_score=0.9,
                    generic_score=0.1,
                    analyzed_at=datetime.utcnow() - timedelta(hours=1)
                ),
                SurveyResponse(
                    id="response-2",
                    question_id="question-2",
                    session_id="session-1",
                    response_text="Another high-quality response with specific examples and detailed explanations.",
                    quality_score=82.0,
                    is_flagged=False,
                    flag_reasons={},
                    gibberish_score=0.2,
                    copy_paste_score=0.1,
                    relevance_score=0.8,
                    generic_score=0.2,
                    analyzed_at=datetime.utcnow() - timedelta(hours=2)
                ),
                # Medium quality responses for session-2
                SurveyResponse(
                    id="response-3",
                    question_id="question-1",
                    session_id="session-2",
                    response_text="This is a decent response with some useful information.",
                    quality_score=65.0,
                    is_flagged=False,
                    flag_reasons={},
                    gibberish_score=0.3,
                    copy_paste_score=0.2,
                    relevance_score=0.6,
                    generic_score=0.3,
                    analyzed_at=datetime.utcnow() - timedelta(hours=3)
                ),
                SurveyResponse(
                    id="response-4",
                    question_id="question-2",
                    session_id="session-2",
                    response_text="Okay response but could be more detailed.",
                    quality_score=58.0,
                    is_flagged=False,
                    flag_reasons={},
                    gibberish_score=0.4,
                    copy_paste_score=0.2,
                    relevance_score=0.5,
                    generic_score=0.4,
                    analyzed_at=datetime.utcnow() - timedelta(hours=4)
                ),
                # Low quality responses for session-3
                SurveyResponse(
                    id="response-5",
                    question_id="question-1",
                    session_id="session-3",
                    response_text="asdfghjkl qwerty random gibberish text",
                    quality_score=12.0,
                    is_flagged=True,
                    flag_reasons={"gibberish": {"score": 0.9, "reason": "Contains random characters"}},
                    gibberish_score=0.9,
                    copy_paste_score=0.1,
                    relevance_score=0.1,
                    generic_score=0.1,
                    analyzed_at=datetime.utcnow() - timedelta(hours=5)
                ),
                SurveyResponse(
                    id="response-6",
                    question_id="question-2",
                    session_id="session-3",
                    response_text="I don't know",
                    quality_score=35.0,
                    is_flagged=True,
                    flag_reasons={"generic": {"score": 0.8, "reason": "Generic response"}},
                    gibberish_score=0.2,
                    copy_paste_score=0.1,
                    relevance_score=0.3,
                    generic_score=0.8,
                    analyzed_at=datetime.utcnow() - timedelta(hours=6)
                )
            ]
            
            for response in responses:
                db.add(response)
            
            await db.commit()
            
            return {
                "sessions": sessions,
                "questions": questions,
                "responses": responses
            }

    @pytest.mark.asyncio
    async def test_end_to_end_dashboard_summary(self, test_db, sample_session_data):
        """Test complete workflow: create data -> generate dashboard summary."""
        async with test_db() as db:
            # Test dashboard summary endpoint
            result = await get_dashboard_summary(
                days=7,
                survey_id="test-survey-1",
                db=db
            )
            
            # Verify aggregated statistics
            assert result["total_responses"] == 6
            assert result["flagged_count"] == 2  # responses 5 and 6
            assert result["flagged_percentage"] == 33.3  # 2/6 * 100
            
            # Verify average quality score (88+82+65+58+12+35)/6 = 56.67
            assert abs(result["avg_quality_score"] - 56.67) < 0.1
            
            # Verify quality distribution buckets
            quality_dist = result["quality_distribution"]
            assert len(quality_dist) == 10
            assert quality_dist["80-90"] == 2  # scores 88, 82
            assert quality_dist["60-70"] == 1  # score 65
            assert quality_dist["50-60"] == 1  # score 58
            assert quality_dist["30-40"] == 1  # score 35
            assert quality_dist["10-20"] == 1  # score 12

    @pytest.mark.asyncio
    async def test_end_to_end_respondent_analysis(self, test_db, sample_session_data):
        """Test complete workflow: create data -> generate respondent analysis."""
        async with test_db() as db:
            # Test respondent analysis endpoint
            result = await get_respondent_analysis(
                survey_id="test-survey-1",
                days=7,
                page=1,
                limit=10,
                db=db
            )
            
            # Verify pagination
            assert len(result["respondents"]) == 3
            assert result["pagination"]["total"] == 3
            assert result["pagination"]["pages"] == 1
            
            # Verify respondent data
            respondents = result["respondents"]
            
            # Session-1: High quality responses
            session1 = next(r for r in respondents if r["session_id"] == "session-1")
            assert session1["response_count"] == 2
            assert session1["flagged_count"] == 0
            assert session1["flagged_percentage"] == 0.0
            assert abs(session1["avg_quality_score"] - 85.0) < 0.1  # (88+82)/2
            assert session1["flag_reasons_summary"] == {}
            
            # Session-2: Medium quality responses
            session2 = next(r for r in respondents if r["session_id"] == "session-2")
            assert session2["response_count"] == 2
            assert session2["flagged_count"] == 0
            assert session2["flagged_percentage"] == 0.0
            assert abs(session2["avg_quality_score"] - 61.5) < 0.1  # (65+58)/2
            assert session2["flag_reasons_summary"] == {}
            
            # Session-3: Low quality responses
            session3 = next(r for r in respondents if r["session_id"] == "session-3")
            assert session3["response_count"] == 2
            assert session3["flagged_count"] == 2
            assert session3["flagged_percentage"] == 100.0
            assert abs(session3["avg_quality_score"] - 23.5) < 0.1  # (12+35)/2
            assert "gibberish" in session3["flag_reasons_summary"]
            assert "generic" in session3["flag_reasons_summary"]
            assert session3["flag_reasons_summary"]["gibberish"] == 1
            assert session3["flag_reasons_summary"]["generic"] == 1

    @pytest.mark.asyncio
    async def test_end_to_end_report_generation(self, test_db, sample_session_data):
        """Test complete workflow: create data -> generate reports with text quality."""
        async with test_db() as db:
            report_service = ReportService()
            
            # Test summary report generation
            summary_report = await report_service.generate_summary_report(
                survey_id="test-survey-1",
                db=db
            )
            
            # Verify summary report includes text quality
            assert summary_report.text_quality_summary is not None
            text_quality = summary_report.text_quality_summary
            
            assert text_quality["total_responses"] == 6
            assert text_quality["flagged_count"] == 2
            assert text_quality["flagged_percentage"] == 33.3
            assert abs(text_quality["avg_quality_score"] - 56.67) < 0.1
            
            # Test detailed report generation
            detailed_report = await report_service.generate_detailed_report(
                survey_id="test-survey-1",
                db=db
            )
            
            # Verify detailed report includes text quality per respondent
            assert len(detailed_report.respondents) == 3
            
            for respondent in detailed_report.respondents:
                assert hasattr(respondent, 'text_response_count')
                assert hasattr(respondent, 'avg_text_quality_score')
                assert hasattr(respondent, 'flagged_text_responses')
                assert hasattr(respondent, 'text_quality_percentage')

    @pytest.mark.asyncio
    async def test_dashboard_api_endpoints_integration(self, client, sample_session_data):
        """Test dashboard API endpoints through HTTP client."""
        # Test dashboard summary endpoint
        response = client.get("/api/v1/text-analysis/dashboard/summary?days=7&survey_id=test-survey-1")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_responses"] == 6
        assert data["flagged_count"] == 2
        assert data["avg_quality_score"] is not None
        
        # Test respondent analysis endpoint
        response = client.get("/api/v1/text-analysis/dashboard/respondents?survey_id=test-survey-1&days=7&page=1&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["respondents"]) == 3
        assert data["pagination"]["total"] == 3
        
        # Verify each respondent has required fields
        for respondent in data["respondents"]:
            assert "session_id" in respondent
            assert "response_count" in respondent
            assert "avg_quality_score" in respondent
            assert "flagged_count" in respondent
            assert "flagged_percentage" in respondent
            assert "flag_reasons_summary" in respondent

    @pytest.mark.asyncio
    async def test_text_quality_filtering_by_survey(self, test_db, sample_session_data):
        """Test that text quality data is correctly filtered by survey ID."""
        async with test_db() as db:
            # Create additional data for different survey
            session_other = Session(
                id="session-other",
                survey_id="test-survey-2",
                respondent_id="respondent-other",
                created_at=datetime.utcnow() - timedelta(days=1),
                is_active=True,
                platform="test"
            )
            db.add(session_other)
            
            response_other = SurveyResponse(
                id="response-other",
                question_id="question-other",
                session_id="session-other",
                response_text="Response for different survey",
                quality_score=95.0,
                is_flagged=False,
                flag_reasons={},
                analyzed_at=datetime.utcnow()
            )
            db.add(response_other)
            await db.commit()
            
            # Test filtering by survey-1
            result = await get_dashboard_summary(
                days=7,
                survey_id="test-survey-1",
                db=db
            )
            
            # Should only include responses from survey-1
            assert result["total_responses"] == 6  # Original 6 responses
            assert result["flagged_count"] == 2    # Original flagged count
            
            # Test filtering by survey-2
            result = await get_dashboard_summary(
                days=7,
                survey_id="test-survey-2",
                db=db
            )
            
            # Should only include responses from survey-2
            assert result["total_responses"] == 1  # Only the new response
            assert result["flagged_count"] == 0    # High quality response
            assert result["avg_quality_score"] == 95.0

    @pytest.mark.asyncio
    async def test_text_quality_date_filtering(self, test_db, sample_session_data):
        """Test that text quality data respects date filtering."""
        async with test_db() as db:
            # Test with very recent date range (should be empty)
            result = await get_dashboard_summary(
                days=0,  # No days back
                survey_id="test-survey-1",
                db=db
            )
            
            assert result["total_responses"] == 0
            assert result["flagged_count"] == 0
            assert result["avg_quality_score"] is None
            
            # Test with longer date range (should include all data)
            result = await get_dashboard_summary(
                days=10,  # 10 days back
                survey_id="test-survey-1",
                db=db
            )
            
            assert result["total_responses"] == 6
            assert result["flagged_count"] == 2

    @pytest.mark.asyncio
    async def test_respondent_analysis_pagination(self, test_db, sample_session_data):
        """Test respondent analysis pagination with text quality data."""
        async with test_db() as db:
            # Test first page
            result = await get_respondent_analysis(
                survey_id="test-survey-1",
                days=7,
                page=1,
                limit=2,
                db=db
            )
            
            assert len(result["respondents"]) == 2
            assert result["pagination"]["page"] == 1
            assert result["pagination"]["limit"] == 2
            assert result["pagination"]["total"] == 3
            assert result["pagination"]["pages"] == 2
            
            # Test second page
            result = await get_respondent_analysis(
                survey_id="test-survey-1",
                days=7,
                page=2,
                limit=2,
                db=db
            )
            
            assert len(result["respondents"]) == 1
            assert result["pagination"]["page"] == 2

    @pytest.mark.asyncio
    async def test_csv_export_with_text_quality(self, test_db, sample_session_data):
        """Test CSV export includes text quality columns."""
        async with test_db() as db:
            report_service = ReportService()
            
            # Generate detailed report
            detailed_report = await report_service.generate_detailed_report(
                survey_id="test-survey-1",
                db=db
            )
            
            # Generate CSV
            csv_content = report_service.generate_csv_report(detailed_report)
            
            # Verify CSV contains text quality columns
            assert "Text Response Count" in csv_content
            assert "Avg Text Quality Score" in csv_content
            assert "Flagged Text Responses" in csv_content
            assert "Text Quality Percentage" in csv_content
            
            # Verify data is present
            lines = csv_content.split('\n')
            assert len(lines) >= 4  # Header + 3 data rows
            
            # Check that we have text quality data in the CSV
            assert "2" in csv_content  # response counts
            assert "85.0" in csv_content or "61.5" in csv_content  # quality scores

    @pytest.mark.asyncio
    async def test_empty_data_scenarios(self, test_db):
        """Test dashboard endpoints with empty data."""
        async with test_db() as db:
            # Test dashboard summary with no data
            result = await get_dashboard_summary(
                days=7,
                survey_id="nonexistent-survey",
                db=db
            )
            
            assert result["total_responses"] == 0
            assert result["avg_quality_score"] is None
            assert result["flagged_count"] == 0
            assert result["flagged_percentage"] == 0.0
            assert result["quality_distribution"] == {}
            
            # Test respondent analysis with no data
            result = await get_respondent_analysis(
                survey_id="nonexistent-survey",
                days=7,
                page=1,
                limit=10,
                db=db
            )
            
            assert result["respondents"] == []
            assert result["pagination"]["total"] == 0
            assert result["pagination"]["pages"] == 0

    @pytest.mark.asyncio
    async def test_performance_with_large_dataset(self, test_db):
        """Test performance with larger dataset."""
        async with test_db() as db:
            # Create larger dataset
            sessions = []
            responses = []
            
            for i in range(50):  # 50 sessions
                session = Session(
                    id=f"perf-session-{i}",
                    survey_id="performance-survey",
                    respondent_id=f"perf-respondent-{i}",
                    created_at=datetime.utcnow() - timedelta(days=i % 7),
                    is_active=True,
                    platform="test"
                )
                sessions.append(session)
                db.add(session)
                
                # 2 responses per session
                for j in range(2):
                    response = SurveyResponse(
                        id=f"perf-response-{i}-{j}",
                        question_id=f"perf-question-{j}",
                        session_id=f"perf-session-{i}",
                        response_text=f"Response {i}-{j}",
                        quality_score=60.0 + (i % 40),  # Scores 60-99
                        is_flagged=(i % 10 == 0),  # Every 10th session flagged
                        flag_reasons={"test": {}} if (i % 10 == 0) else {},
                        analyzed_at=datetime.utcnow() - timedelta(hours=i)
                    )
                    responses.append(response)
                    db.add(response)
            
            await db.commit()
            
            # Test dashboard summary performance
            import time
            start_time = time.time()
            
            result = await get_dashboard_summary(
                days=7,
                survey_id="performance-survey",
                db=db
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Should complete within reasonable time (< 2 seconds)
            assert execution_time < 2.0
            
            # Verify results
            assert result["total_responses"] == 100  # 50 sessions * 2 responses
            assert result["flagged_count"] == 10     # Every 10th session flagged
            
            # Test respondent analysis performance
            start_time = time.time()
            
            result = await get_respondent_analysis(
                survey_id="performance-survey",
                days=7,
                page=1,
                limit=25,
                db=db
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Should complete within reasonable time
            assert execution_time < 2.0
            
            # Verify pagination
            assert len(result["respondents"]) == 25  # First page
            assert result["pagination"]["total"] == 50  # Total sessions
            assert result["pagination"]["pages"] == 2   # 50/25 = 2 pages
