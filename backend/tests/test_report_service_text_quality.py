"""
Test suite for report service text quality integration.

This module tests the enhanced report service functionality that includes
text quality analysis data in summary and detailed reports.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from unittest.mock import AsyncMock, patch, Mock
import json

# Minimal grid/timing summaries for report service tests (fraud/grid/timing integration)
GRID_SUMMARY_MOCK = {"survey_id": "", "total_responses": 0, "straight_lined_count": 0, "straight_lined_percentage": 0.0, "pattern_distribution": {}, "avg_variance_score": 0.0, "avg_satisficing_score": 0.0, "unique_questions": 0}
TIMING_SUMMARY_MOCK = {"survey_id": "", "total_analyses": 0, "speeders_count": 0, "speeders_percentage": 0.0, "flatliners_count": 0, "flatliners_percentage": 0.0, "anomalies_count": 0, "anomalies_percentage": 0.0, "avg_response_time_ms": 0.0, "median_response_time_ms": 0.0, "unique_questions": 0}

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.report_service import ReportService
from app.models import Session, BehaviorData, DetectionResult, SurveyResponse, SurveyQuestion
from app.models.report_models import SurveySummaryReport, DetailedReport, RespondentDetail


class TestReportServiceTextQuality:
    """Test class for report service text quality integration."""

    @pytest.fixture
    def report_service(self):
        """Create report service instance."""
        return ReportService()

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def patch_aggregation_for_report(self, report_service):
        """Patch aggregation service so summary report fraud/grid/timing calls do not hit DB."""
        with patch.object(report_service.aggregation_service, "get_grid_analysis_summary", new_callable=AsyncMock, return_value=GRID_SUMMARY_MOCK), \
             patch.object(report_service.aggregation_service, "get_timing_analysis_summary", new_callable=AsyncMock, return_value=TIMING_SUMMARY_MOCK):
            yield

    @pytest.fixture
    def mock_fraud_result_empty(self):
        """Mock execute result for fraud query (no indicators)."""
        m = Mock()
        m.scalars.return_value.all.return_value = []
        return m

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
                last_activity=now - timedelta(hours=1),
                is_active=True,
                platform="test",
                behavior_data=[],
                detection_results=[]
            ),
            Session(
                id="session-2",
                survey_id="survey-1", 
                respondent_id="respondent-2",
                created_at=now - timedelta(days=2),
                last_activity=now - timedelta(hours=2),
                is_active=True,
                platform="test",
                behavior_data=[],
                detection_results=[]
            ),
            Session(
                id="session-3",
                survey_id="survey-2",
                respondent_id="respondent-3", 
                created_at=now - timedelta(days=3),
                last_activity=now - timedelta(hours=3),
                is_active=True,
                platform="test",
                behavior_data=[],
                detection_results=[]
            )
        ]

    @pytest.fixture
    def sample_detection_results(self, sample_sessions):
        """Create sample detection results."""
        return [
            DetectionResult(
                id="detection-1",
                session_id="session-1",
                is_bot=False,
                confidence_score=0.85,
                risk_level="low",
                method_scores={"keystroke_analysis": 0.2, "mouse_analysis": 0.1},
                analysis_summary="Human-like behavior detected",
                created_at=datetime.utcnow()
            ),
            DetectionResult(
                id="detection-2",
                session_id="session-2",
                is_bot=True,
                confidence_score=0.92,
                risk_level="high",
                method_scores={"keystroke_analysis": 0.9, "mouse_analysis": 0.8},
                analysis_summary="Bot behavior detected",
                created_at=datetime.utcnow()
            ),
            DetectionResult(
                id="detection-3",
                session_id="session-3",
                is_bot=False,
                confidence_score=0.75,
                risk_level="medium",
                method_scores={"keystroke_analysis": 0.3, "mouse_analysis": 0.4},
                analysis_summary="Suspicious but human behavior",
                created_at=datetime.utcnow()
            )
        ]

    @pytest.fixture
    def sample_survey_responses(self, sample_sessions):
        """Create sample survey responses with text quality data."""
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
                gibberish_score=0.1,
                copy_paste_score=0.2,
                relevance_score=0.9,
                generic_score=0.1,
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
                gibberish_score=0.2,
                copy_paste_score=0.1,
                relevance_score=0.8,
                generic_score=0.2,
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
                gibberish_score=0.3,
                copy_paste_score=0.2,
                relevance_score=0.7,
                generic_score=0.3,
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
                gibberish_score=0.8,
                copy_paste_score=0.1,
                relevance_score=0.2,
                generic_score=0.1,
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
                gibberish_score=0.1,
                copy_paste_score=0.2,
                relevance_score=0.1,
                generic_score=0.3,
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
                gibberish_score=0.2,
                copy_paste_score=0.1,
                relevance_score=0.4,
                generic_score=0.7,
                analyzed_at=now - timedelta(hours=6)
            )
        ]

    @pytest.mark.asyncio
    async def test_generate_summary_report_with_text_quality(self, report_service, mock_db_session, 
                                                           sample_sessions, sample_detection_results, 
                                                           sample_survey_responses, patch_aggregation_for_report,
                                                           mock_fraud_result_empty):
        """Test summary report generation includes text quality data."""
        # Setup session query mock - fix async mock setup
        mock_session_result = Mock()
        mock_session_result.scalars.return_value.all.return_value = sample_sessions
        
        # Setup detection query mock
        detection_query_mock = Mock()
        detection_query_mock.scalars.return_value.all.return_value = sample_detection_results
        # Setup multiple query mocks
        mock_activity_result = Mock()
        mock_activity_result.all.return_value = [("keystroke", 100), ("mouse_click", 50)]
        
        mock_event_count_result1 = Mock()
        mock_event_count_result1.scalar.return_value = 10
        
        mock_event_count_result2 = Mock()
        mock_event_count_result2.scalar.return_value = 15
        
        mock_event_count_result3 = Mock()
        mock_event_count_result3.scalar.return_value = 8
        
        mock_text_responses_result = Mock()
        mock_text_responses_result.scalars.return_value.all.return_value = sample_survey_responses
        
        mock_db_session.execute.side_effect = [
            # First call for sessions
            mock_session_result,
            # Second call for detections
            detection_query_mock,
            # Third call for activity distribution
            mock_activity_result,
            # Fourth call for event count (session 1)
            mock_event_count_result1,
            # Fifth call for event count (session 2)
            mock_event_count_result2,
            # Sixth call for event count (session 3)
            mock_event_count_result3,
            # Seventh call for text responses
            mock_text_responses_result,
            # Eighth call for fraud aggregation
            mock_fraud_result_empty,
        ]
        
        result = await report_service.generate_summary_report(
            survey_id="survey-1",
            db=mock_db_session
        )
        
        # Verify basic report data
        assert isinstance(result, SurveySummaryReport)
        assert result.survey_id == "survey-1"
        assert result.total_sessions == 3
        assert result.bot_detections == 1
        assert result.human_respondents == 2
        
        # Verify text quality summary is included
        assert result.text_quality_summary is not None
        text_quality = result.text_quality_summary
        
        # Verify text quality metrics
        assert text_quality["total_responses"] == 6
        assert text_quality["flagged_count"] == 3
        assert text_quality["flagged_percentage"] == 50.0
        assert text_quality["avg_quality_score"] == 52.5  # (85+78+72+15+25+40)/6
        
        # Verify quality distribution
        quality_dist = text_quality["quality_distribution"]
        assert "0-10" in quality_dist
        assert "80-90" in quality_dist
        assert quality_dist["80-90"] == 1  # score 85
        assert quality_dist["70-80"] == 2  # scores 78, 72

    @pytest.mark.asyncio
    async def test_generate_summary_report_no_text_responses(self, report_service, mock_db_session, 
                                                           sample_sessions, sample_detection_results,
                                                           patch_aggregation_for_report, mock_fraud_result_empty):
        """Test summary report when no text responses exist."""
        # Setup mocks - fix async mock setup
        mock_session_result = Mock()
        mock_session_result.scalars.return_value.all.return_value = sample_sessions
        
        mock_detection_result = Mock()
        mock_detection_result.scalars.return_value.all.return_value = sample_detection_results
        
        mock_activity_result = Mock()
        mock_activity_result.all.return_value = [("keystroke", 100)]
        
        mock_event_results = [
            Mock(scalar=Mock(return_value=10)),
            Mock(scalar=Mock(return_value=15)),
            Mock(scalar=Mock(return_value=8))
        ]
        
        mock_empty_text_result = Mock()
        mock_empty_text_result.scalars.return_value.all.return_value = []
        
        mock_db_session.execute.side_effect = [
            # Sessions
            mock_session_result,
            # Detections
            mock_detection_result,
            # Activity distribution
            mock_activity_result,
            # Event counts (3 calls)
            mock_event_results[0],
            mock_event_results[1],
            mock_event_results[2],
            # Text responses (empty)
            mock_empty_text_result,
            # Fraud aggregation
            mock_fraud_result_empty,
        ]
        
        result = await report_service.generate_summary_report(
            survey_id="survey-1",
            db=mock_db_session
        )
        
        # Verify text quality summary is None when no responses
        assert result.text_quality_summary is None

    @pytest.mark.asyncio
    async def test_generate_summary_report_filtered_survey(self, report_service, mock_db_session, 
                                                          sample_sessions, sample_detection_results, 
                                                          sample_survey_responses, patch_aggregation_for_report,
                                                          mock_fraud_result_empty):
        """Test summary report with survey filtering includes only relevant text responses."""
        # Filter to survey-1 sessions only
        survey1_sessions = [s for s in sample_sessions if s.survey_id == "survey-1"]
        survey1_responses = [r for r in sample_survey_responses if r.session_id in ["session-1", "session-2"]]
        
        # Setup mocks - fix async mock setup
        mock_session_result = Mock()
        mock_session_result.scalars.return_value.all.return_value = survey1_sessions
        
        mock_detection_result = Mock()
        mock_detection_result.scalars.return_value.all.return_value = sample_detection_results[:2]
        
        mock_activity_result = Mock()
        mock_activity_result.all.return_value = [("keystroke", 80)]
        
        mock_event_results = [
            Mock(scalar=Mock(return_value=10)),
            Mock(scalar=Mock(return_value=15))
        ]
        
        mock_text_responses_result = Mock()
        mock_text_responses_result.scalars.return_value.all.return_value = survey1_responses
        
        mock_db_session.execute.side_effect = [
            # Sessions
            mock_session_result,
            # Detections
            mock_detection_result,
            # Activity distribution
            mock_activity_result,
            # Event counts (2 calls)
            mock_event_results[0],
            mock_event_results[1],
            # Text responses for survey-1 only
            mock_text_responses_result,
            # Fraud aggregation
            mock_fraud_result_empty,
        ]
        
        result = await report_service.generate_summary_report(
            survey_id="survey-1",
            db=mock_db_session
        )
        
        # Verify only survey-1 text responses are included
        text_quality = result.text_quality_summary
        assert text_quality["total_responses"] == 4  # Only session-1 and session-2 responses
        assert text_quality["flagged_count"] == 1  # Only response-4 is flagged

    @pytest.mark.asyncio
    async def test_generate_detailed_report_with_text_quality(self, report_service, mock_db_session, 
                                                            sample_sessions, sample_detection_results):
        """Test detailed report generation includes text quality fields in respondent details."""
        # Setup session with related data
        session_with_data = sample_sessions[0]
        session_with_data.behavior_data = [
            BehaviorData(
                id="behavior-1",
                session_id="session-1",
                event_type="keystroke",
                timestamp=datetime.utcnow(),
                element_id="input-1",
                page_url="https://test.com",
                page_title="Test Page"
            ),
            BehaviorData(
                id="behavior-2", 
                session_id="session-1",
                event_type="mouse_click",
                timestamp=datetime.utcnow(),
                element_id="button-1",
                page_url="https://test.com",
                page_title="Test Page"
            )
        ]
        session_with_data.detection_results = [sample_detection_results[0]]
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [session_with_data]
        mock_text = Mock()
        mock_text.scalars.return_value.all.return_value = []
        mock_fraud_first = Mock()
        mock_fraud_first.scalars.return_value.first.return_value = None
        mock_grid = Mock()
        mock_grid.scalars.return_value.all.return_value = []
        mock_timing = Mock()
        mock_timing.scalar.return_value = 0
        mock_db_session.execute.side_effect = [
            mock_result,
            mock_text, mock_fraud_first, mock_grid, mock_timing, mock_timing, mock_timing,
        ]
        
        result = await report_service.generate_detailed_report(
            survey_id="survey-1",
            db=mock_db_session
        )
        
        # Verify detailed report structure
        assert isinstance(result, DetailedReport)
        assert result.survey_id == "survey-1"
        assert len(result.respondents) == 1
        
        # Verify respondent detail has text quality fields
        respondent = result.respondents[0]
        assert hasattr(respondent, 'text_response_count')
        assert hasattr(respondent, 'avg_text_quality_score')
        assert hasattr(respondent, 'flagged_text_responses')
        assert hasattr(respondent, 'text_quality_percentage')

    @pytest.mark.asyncio
    async def test_generate_csv_report_includes_text_quality(self, report_service, sample_sessions, 
                                                           sample_detection_results, sample_survey_responses):
        """Test CSV report generation includes text quality columns."""
        # Create detailed report with text quality data
        respondents = [
            RespondentDetail(
                session_id="session-1",
                respondent_id="respondent-1",
                created_at=datetime.utcnow() - timedelta(days=1),
                last_activity=datetime.utcnow() - timedelta(hours=1),
                is_bot=False,
                confidence_score=0.85,
                risk_level="low",
                total_events=10,
                session_duration_minutes=15.5,
                event_breakdown={"keystroke": 5, "mouse_click": 3, "scroll": 2},
                method_scores={"keystroke_analysis": 0.2},
                flagged_patterns=None,
                analysis_summary="Human-like behavior",
                bot_explanation=None,
                text_response_count=2,
                avg_text_quality_score=81.5,
                flagged_text_responses=0,
                text_quality_percentage=0.0
            ),
            RespondentDetail(
                session_id="session-2",
                respondent_id="respondent-2",
                created_at=datetime.utcnow() - timedelta(days=2),
                last_activity=datetime.utcnow() - timedelta(hours=2),
                is_bot=True,
                confidence_score=0.92,
                risk_level="high",
                total_events=15,
                session_duration_minutes=8.2,
                event_breakdown={"keystroke": 2, "mouse_click": 1, "scroll": 12},
                method_scores={"keystroke_analysis": 0.9},
                flagged_patterns={"rapid_typing": {"count": 5}},
                analysis_summary="Bot behavior detected",
                bot_explanation="rapid_typing: 5 suspicious events (high severity)",
                text_response_count=2,
                avg_text_quality_score=43.5,
                flagged_text_responses=1,
                text_quality_percentage=50.0
            )
        ]
        
        detailed_report = DetailedReport(
            survey_id="survey-1",
            total_respondents=2,
            generated_at=datetime.utcnow(),
            summary_stats={"total_sessions": 2, "bot_detections": 1},
            respondents=respondents
        )
        
        csv_content = report_service.generate_csv_report(detailed_report)
        
        # Verify CSV contains text quality columns
        assert "Text Response Count" in csv_content
        assert "Avg Text Quality Score" in csv_content
        assert "Flagged Text Responses" in csv_content
        assert "Text Quality Percentage" in csv_content
        
        # Verify data is included
        lines = csv_content.split('\n')
        assert len(lines) >= 3  # Header + 2 data rows
        
        # Check specific values
        assert "2" in lines[1]  # text_response_count for first respondent
        assert "81.5" in lines[1]  # avg_text_quality_score for first respondent
        assert "0" in lines[1]  # flagged_text_responses for first respondent
        
        assert "2" in lines[2]  # text_response_count for second respondent
        assert "43.5" in lines[2]  # avg_text_quality_score for second respondent
        assert "1" in lines[2]  # flagged_text_responses for second respondent

    @pytest.mark.asyncio
    async def test_generate_summary_report_date_filtering(self, report_service, mock_db_session):
        """Test summary report respects date filtering for text responses."""
        now = datetime.utcnow()
        date_from = now - timedelta(days=2)
        date_to = now - timedelta(days=1)
        
        # Create responses outside date range
        old_responses = [
            SurveyResponse(
                id="response-old",
                question_id="question-1",
                session_id="session-1",
                response_text="Old response",
                quality_score=60.0,
                is_flagged=False,
                flag_reasons={},
                analyzed_at=now - timedelta(days=3)  # Outside range
            )
        ]
        
        # Setup mocks for empty data scenario
        mock_empty_session_result = Mock()
        mock_empty_session_result.scalars.return_value.all.return_value = []
        
        mock_empty_text_result = Mock()
        mock_empty_text_result.scalars.return_value.all.return_value = []
        
        mock_db_session.execute.side_effect = [
            # Sessions (empty due to date filter)
            mock_empty_session_result,
            # Text responses (empty)
            mock_empty_text_result
        ]
        
        result = await report_service.generate_summary_report(
            survey_id="survey-1",
            db=mock_db_session,
            date_from=date_from,
            date_to=date_to
        )
        
        # Verify no text quality data when no sessions in date range
        assert result.text_quality_summary is None

    @pytest.mark.asyncio
    async def test_generate_summary_report_quality_distribution_calculation(self, report_service, 
                                                                          mock_db_session, sample_sessions):
        """Test quality distribution calculation in summary reports."""
        # Create responses with specific quality scores for testing distribution
        test_responses = [
            SurveyResponse(
                id="response-1", question_id="q1", session_id="session-1",
                response_text="Score 95", quality_score=95.0, is_flagged=False,
                flag_reasons={}, analyzed_at=datetime.utcnow()
            ),
            SurveyResponse(
                id="response-2", question_id="q2", session_id="session-1", 
                response_text="Score 85", quality_score=85.0, is_flagged=False,
                flag_reasons={}, analyzed_at=datetime.utcnow()
            ),
            SurveyResponse(
                id="response-3", question_id="q3", session_id="session-1",
                response_text="Score 75", quality_score=75.0, is_flagged=False,
                flag_reasons={}, analyzed_at=datetime.utcnow()
            ),
            SurveyResponse(
                id="response-4", question_id="q4", session_id="session-1",
                response_text="Score 25", quality_score=25.0, is_flagged=True,
                flag_reasons={"low_quality": {}}, analyzed_at=datetime.utcnow()
            ),
            SurveyResponse(
                id="response-5", question_id="q5", session_id="session-1",
                response_text="Score 5", quality_score=5.0, is_flagged=True,
                flag_reasons={"gibberish": {}}, analyzed_at=datetime.utcnow()
            )
        ]
        
        # Setup mocks for quality distribution test
        mock_session_result = Mock()
        mock_session_result.scalars.return_value.all.return_value = sample_sessions
        
        mock_empty_detection_result = Mock()
        mock_empty_detection_result.scalars.return_value.all.return_value = []
        
        mock_empty_activity_result = Mock()
        mock_empty_activity_result.all.return_value = []
        
        mock_empty_event_results = [
            Mock(scalar=Mock(return_value=0)),
            Mock(scalar=Mock(return_value=0)),
            Mock(scalar=Mock(return_value=0))
        ]
        
        mock_test_responses_result = Mock()
        mock_test_responses_result.scalars.return_value.all.return_value = test_responses
        
        mock_fraud_empty = Mock()
        mock_fraud_empty.scalars.return_value.all.return_value = []
        
        mock_db_session.execute.side_effect = [
            # Sessions
            mock_session_result,
            # Detections
            mock_empty_detection_result,
            # Activity distribution
            mock_empty_activity_result,
            # Event counts (3 calls)
            mock_empty_event_results[0],
            mock_empty_event_results[1],
            mock_empty_event_results[2],
            # Text responses
            mock_test_responses_result,
            # Fraud aggregation
            mock_fraud_empty,
        ]
        
        with patch.object(report_service.aggregation_service, "get_grid_analysis_summary", new_callable=AsyncMock, return_value=GRID_SUMMARY_MOCK), \
             patch.object(report_service.aggregation_service, "get_timing_analysis_summary", new_callable=AsyncMock, return_value=TIMING_SUMMARY_MOCK):
            result = await report_service.generate_summary_report(
                survey_id="survey-1",
                db=mock_db_session
            )
        
        # Verify quality distribution
        quality_dist = result.text_quality_summary["quality_distribution"]
        
        # Check specific bucket counts
        assert quality_dist["90-100"] == 1  # score 95
        assert quality_dist["80-90"] == 1   # score 85
        assert quality_dist["70-80"] == 1   # score 75
        assert quality_dist["20-30"] == 1   # score 25
        assert quality_dist["0-10"] == 1    # score 5
        
        # Verify other buckets are 0
        assert quality_dist["10-20"] == 0
        assert quality_dist["30-40"] == 0
        assert quality_dist["40-50"] == 0
        assert quality_dist["50-60"] == 0
        assert quality_dist["60-70"] == 0

    @pytest.mark.asyncio
    async def test_generate_summary_report_error_handling(self, report_service, mock_db_session):
        """Test error handling in summary report generation."""
        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database connection error")
        
        with pytest.raises(Exception) as exc_info:
            await report_service.generate_summary_report(
                survey_id="survey-1",
                db=mock_db_session
            )
        
        assert "Database connection error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_detailed_report_error_handling(self, report_service, mock_db_session):
        """Test error handling in detailed report generation."""
        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database connection error")
        
        with pytest.raises(Exception) as exc_info:
            await report_service.generate_detailed_report(
                survey_id="survey-1",
                db=mock_db_session
            )
        
        assert "Database connection error" in str(exc_info.value)
