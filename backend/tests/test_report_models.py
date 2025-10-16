"""
Test suite for report models with text quality integration.

This module tests the enhanced Pydantic models that include text quality
analysis fields in survey reports and respondent details.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.report_models import (
    SurveySummaryReport, DetailedReport, RespondentDetail,
    ReportRequest, ReportResponse, ReportType, ReportFormat,
    SurveyListResponse
)


class TestReportModels:
    """Test class for report models validation."""

    def test_survey_summary_report_with_text_quality(self):
        """Test SurveySummaryReport with text quality summary."""
        now = datetime.utcnow()
        
        text_quality_summary = {
            "total_responses": 150,
            "avg_quality_score": 72.5,
            "flagged_count": 23,
            "flagged_percentage": 15.3,
            "quality_distribution": {
                "0-10": 5,
                "10-20": 8,
                "20-30": 12,
                "30-40": 15,
                "40-50": 18,
                "50-60": 22,
                "60-70": 25,
                "70-80": 20,
                "80-90": 15,
                "90-100": 10
            }
        }
        
        report = SurveySummaryReport(
            survey_id="survey-123",
            survey_name="Customer Satisfaction Survey",
            total_respondents=200,
            total_sessions=200,
            bot_detections=15,
            human_respondents=185,
            bot_detection_rate=7.5,
            activity_distribution={
                "keystroke": 5000,
                "mouse_click": 2500,
                "scroll": 1800
            },
            risk_distribution={
                "low": 160,
                "medium": 30,
                "high": 10
            },
            platform="qualtrics",
            date_range={
                "from": (now - timedelta(days=30)).isoformat(),
                "to": now.isoformat()
            },
            average_session_duration=12.5,
            average_events_per_session=45.5,
            text_quality_summary=text_quality_summary
        )
        
        # Verify basic fields
        assert report.survey_id == "survey-123"
        assert report.total_respondents == 200
        assert report.bot_detections == 15
        assert report.bot_detection_rate == 7.5
        
        # Verify text quality summary
        assert report.text_quality_summary is not None
        assert report.text_quality_summary["total_responses"] == 150
        assert report.text_quality_summary["avg_quality_score"] == 72.5
        assert report.text_quality_summary["flagged_count"] == 23
        assert report.text_quality_summary["flagged_percentage"] == 15.3
        
        # Verify quality distribution
        quality_dist = report.text_quality_summary["quality_distribution"]
        assert len(quality_dist) == 10
        assert quality_dist["0-10"] == 5
        assert quality_dist["90-100"] == 10

    def test_survey_summary_report_without_text_quality(self):
        """Test SurveySummaryReport without text quality summary."""
        now = datetime.utcnow()
        
        report = SurveySummaryReport(
            survey_id="survey-456",
            total_respondents=100,
            total_sessions=100,
            bot_detections=5,
            human_respondents=95,
            bot_detection_rate=5.0,
            activity_distribution={"keystroke": 2000},
            risk_distribution={"low": 95, "medium": 5},
            date_range={
                "from": (now - timedelta(days=7)).isoformat(),
                "to": now.isoformat()
            },
            text_quality_summary=None  # No text quality data
        )
        
        assert report.survey_id == "survey-456"
        assert report.text_quality_summary is None

    def test_respondent_detail_with_text_quality(self):
        """Test RespondentDetail with text quality fields."""
        now = datetime.utcnow()
        
        respondent = RespondentDetail(
            session_id="session-789",
            respondent_id="respondent-123",
            created_at=now - timedelta(days=1),
            last_activity=now - timedelta(hours=2),
            is_bot=False,
            confidence_score=0.85,
            risk_level="low",
            total_events=45,
            session_duration_minutes=18.5,
            event_breakdown={
                "keystroke": 20,
                "mouse_click": 15,
                "scroll": 10
            },
            method_scores={
                "keystroke_analysis": 0.2,
                "mouse_analysis": 0.1,
                "timing_analysis": 0.3
            },
            flagged_patterns=None,
            analysis_summary="Human-like behavior detected",
            bot_explanation=None,
            text_response_count=3,
            avg_text_quality_score=78.5,
            flagged_text_responses=1,
            text_quality_percentage=33.3
        )
        
        # Verify basic fields
        assert respondent.session_id == "session-789"
        assert respondent.respondent_id == "respondent-123"
        assert respondent.is_bot is False
        assert respondent.confidence_score == 0.85
        assert respondent.risk_level == "low"
        
        # Verify text quality fields
        assert respondent.text_response_count == 3
        assert respondent.avg_text_quality_score == 78.5
        assert respondent.flagged_text_responses == 1
        assert respondent.text_quality_percentage == 33.3

    def test_respondent_detail_without_text_quality(self):
        """Test RespondentDetail without text quality data."""
        now = datetime.utcnow()
        
        respondent = RespondentDetail(
            session_id="session-999",
            respondent_id="respondent-456",
            created_at=now - timedelta(days=2),
            last_activity=now - timedelta(hours=1),
            is_bot=True,
            confidence_score=0.92,
            risk_level="high",
            total_events=25,
            session_duration_minutes=5.2,
            event_breakdown={"keystroke": 10, "mouse_click": 5},
            method_scores={"keystroke_analysis": 0.9},
            flagged_patterns={"rapid_typing": {"count": 8}},
            analysis_summary="Bot behavior detected",
            bot_explanation="rapid_typing: 8 suspicious events",
            text_response_count=None,  # No text responses
            avg_text_quality_score=None,
            flagged_text_responses=None,
            text_quality_percentage=None
        )
        
        # Verify basic fields
        assert respondent.is_bot is True
        assert respondent.confidence_score == 0.92
        assert respondent.risk_level == "high"
        
        # Verify text quality fields are None
        assert respondent.text_response_count is None
        assert respondent.avg_text_quality_score is None
        assert respondent.flagged_text_responses is None
        assert respondent.text_quality_percentage is None

    def test_detailed_report_with_text_quality(self):
        """Test DetailedReport with respondents having text quality data."""
        now = datetime.utcnow()
        
        respondents = [
            RespondentDetail(
                session_id="session-1",
                respondent_id="respondent-1",
                created_at=now - timedelta(days=1),
                last_activity=now - timedelta(hours=1),
                is_bot=False,
                confidence_score=0.8,
                risk_level="low",
                total_events=30,
                session_duration_minutes=15.0,
                event_breakdown={"keystroke": 15, "mouse_click": 10},
                method_scores={"keystroke_analysis": 0.2},
                flagged_patterns=None,
                analysis_summary="Human behavior",
                bot_explanation=None,
                text_response_count=2,
                avg_text_quality_score=85.0,
                flagged_text_responses=0,
                text_quality_percentage=0.0
            ),
            RespondentDetail(
                session_id="session-2",
                respondent_id="respondent-2",
                created_at=now - timedelta(days=2),
                last_activity=now - timedelta(hours=2),
                is_bot=True,
                confidence_score=0.9,
                risk_level="high",
                total_events=20,
                session_duration_minutes=8.0,
                event_breakdown={"keystroke": 5, "mouse_click": 5},
                method_scores={"keystroke_analysis": 0.8},
                flagged_patterns={"rapid_typing": {"count": 3}},
                analysis_summary="Bot behavior",
                bot_explanation="rapid_typing: 3 suspicious events",
                text_response_count=2,
                avg_text_quality_score=25.0,
                flagged_text_responses=2,
                text_quality_percentage=100.0
            )
        ]
        
        detailed_report = DetailedReport(
            survey_id="survey-789",
            survey_name="Test Survey",
            total_respondents=2,
            generated_at=now,
            summary_stats={
                "total_sessions": 2,
                "bot_detections": 1,
                "human_respondents": 1,
                "bot_detection_rate": 50.0,
                "risk_distribution": {"low": 1, "high": 1},
                "activity_distribution": {"keystroke": 35, "mouse_click": 20}
            },
            respondents=respondents
        )
        
        # Verify report structure
        assert detailed_report.survey_id == "survey-789"
        assert detailed_report.total_respondents == 2
        assert len(detailed_report.respondents) == 2
        
        # Verify respondents have text quality data
        respondent1 = detailed_report.respondents[0]
        assert respondent1.text_response_count == 2
        assert respondent1.avg_text_quality_score == 85.0
        assert respondent1.flagged_text_responses == 0
        
        respondent2 = detailed_report.respondents[1]
        assert respondent2.text_response_count == 2
        assert respondent2.avg_text_quality_score == 25.0
        assert respondent2.flagged_text_responses == 2

    def test_report_request_validation(self):
        """Test ReportRequest model validation."""
        now = datetime.utcnow()
        
        request = ReportRequest(
            survey_id="survey-123",
            report_type=ReportType.SUMMARY,
            format=ReportFormat.JSON,
            include_inactive=False,
            date_from=now - timedelta(days=30),
            date_to=now
        )
        
        assert request.survey_id == "survey-123"
        assert request.report_type == ReportType.SUMMARY
        assert request.format == ReportFormat.JSON
        assert request.include_inactive is False
        assert request.date_from is not None
        assert request.date_to is not None

    def test_report_response_success(self):
        """Test ReportResponse model for successful report generation."""
        now = datetime.utcnow()
        
        text_quality_summary = {
            "total_responses": 100,
            "avg_quality_score": 75.0,
            "flagged_count": 10,
            "flagged_percentage": 10.0,
            "quality_distribution": {"70-80": 30, "80-90": 20}
        }
        
        summary_data = SurveySummaryReport(
            survey_id="survey-123",
            total_respondents=150,
            total_sessions=150,
            bot_detections=10,
            human_respondents=140,
            bot_detection_rate=6.67,
            activity_distribution={"keystroke": 3000},
            risk_distribution={"low": 140, "medium": 10},
            date_range={"from": now.isoformat(), "to": now.isoformat()},
            text_quality_summary=text_quality_summary
        )
        
        response = ReportResponse(
            success=True,
            report_type=ReportType.SUMMARY,
            format=ReportFormat.JSON,
            generated_at=now,
            summary_data=summary_data,
            detailed_data=None,
            download_url=None,
            file_size=None,
            error_message=None
        )
        
        assert response.success is True
        assert response.report_type == ReportType.SUMMARY
        assert response.format == ReportFormat.JSON
        assert response.summary_data is not None
        assert response.summary_data.text_quality_summary is not None
        assert response.error_message is None

    def test_report_response_error(self):
        """Test ReportResponse model for failed report generation."""
        now = datetime.utcnow()
        
        response = ReportResponse(
            success=False,
            report_type=ReportType.DETAILED,
            format=ReportFormat.CSV,
            generated_at=now,
            summary_data=None,
            detailed_data=None,
            download_url=None,
            file_size=None,
            error_message="Database connection failed"
        )
        
        assert response.success is False
        assert response.error_message == "Database connection failed"
        assert response.summary_data is None
        assert response.detailed_data is None

    def test_survey_list_response(self):
        """Test SurveyListResponse model."""
        surveys = [
            {
                "survey_id": "survey-1",
                "platform": "qualtrics",
                "session_count": 150,
                "bot_count": 10,
                "human_count": 140,
                "bot_rate": 6.67,
                "first_session": "2024-01-01T00:00:00Z",
                "last_session": "2024-01-31T23:59:59Z"
            },
            {
                "survey_id": "survey-2",
                "platform": "decipher",
                "session_count": 75,
                "bot_count": 5,
                "human_count": 70,
                "bot_rate": 6.67,
                "first_session": "2024-01-15T00:00:00Z",
                "last_session": "2024-01-31T23:59:59Z"
            }
        ]
        
        response = SurveyListResponse(
            surveys=surveys,
            total_count=2
        )
        
        assert len(response.surveys) == 2
        assert response.total_count == 2
        assert response.surveys[0]["survey_id"] == "survey-1"
        assert response.surveys[1]["survey_id"] == "survey-2"

    def test_text_quality_summary_validation(self):
        """Test text quality summary data validation."""
        # Test valid text quality summary
        valid_summary = {
            "total_responses": 100,
            "avg_quality_score": 75.5,
            "flagged_count": 15,
            "flagged_percentage": 15.0,
            "quality_distribution": {
                "0-10": 5,
                "10-20": 8,
                "20-30": 12,
                "30-40": 15,
                "40-50": 18,
                "50-60": 22,
                "60-70": 25,
                "70-80": 20,
                "80-90": 15,
                "90-100": 10
            }
        }
        
        report = SurveySummaryReport(
            survey_id="test-survey",
            total_respondents=150,
            total_sessions=150,
            bot_detections=10,
            human_respondents=140,
            bot_detection_rate=6.67,
            activity_distribution={"keystroke": 1000},
            risk_distribution={"low": 140, "medium": 10},
            date_range={"from": "2024-01-01T00:00:00Z", "to": "2024-01-31T23:59:59Z"},
            text_quality_summary=valid_summary
        )
        
        assert report.text_quality_summary["total_responses"] == 100
        assert report.text_quality_summary["avg_quality_score"] == 75.5
        assert len(report.text_quality_summary["quality_distribution"]) == 10

    def test_respondent_detail_text_quality_edge_cases(self):
        """Test RespondentDetail with edge cases for text quality fields."""
        now = datetime.utcnow()
        
        # Test with zero values
        respondent_zero = RespondentDetail(
            session_id="session-zero",
            respondent_id="respondent-zero",
            created_at=now,
            last_activity=now,
            is_bot=False,
            confidence_score=0.5,
            risk_level="medium",
            total_events=0,
            session_duration_minutes=0.0,
            event_breakdown={},
            method_scores={},
            flagged_patterns=None,
            analysis_summary=None,
            bot_explanation=None,
            text_response_count=0,
            avg_text_quality_score=0.0,
            flagged_text_responses=0,
            text_quality_percentage=0.0
        )
        
        assert respondent_zero.text_response_count == 0
        assert respondent_zero.avg_text_quality_score == 0.0
        assert respondent_zero.flagged_text_responses == 0
        assert respondent_zero.text_quality_percentage == 0.0

    def test_model_serialization(self):
        """Test model serialization with datetime fields."""
        now = datetime.utcnow()
        
        respondent = RespondentDetail(
            session_id="session-serialization",
            respondent_id="respondent-serialization",
            created_at=now,
            last_activity=now,
            is_bot=False,
            confidence_score=0.8,
            risk_level="low",
            total_events=10,
            session_duration_minutes=5.0,
            event_breakdown={"keystroke": 5},
            method_scores={"keystroke_analysis": 0.2},
            flagged_patterns=None,
            analysis_summary="Test analysis",
            bot_explanation=None,
            text_response_count=1,
            avg_text_quality_score=80.0,
            flagged_text_responses=0,
            text_quality_percentage=0.0
        )
        
        # Test JSON serialization
        json_data = respondent.model_dump()
        assert json_data["text_response_count"] == 1
        assert json_data["avg_text_quality_score"] == 80.0
        
        # Test JSON serialization with mode='json' to convert datetime to string
        json_data_str = respondent.model_dump(mode='json')
        assert isinstance(json_data_str["created_at"], str)
        assert isinstance(json_data_str["last_activity"], str)

    def test_invalid_report_type_validation(self):
        """Test validation with invalid report type."""
        with pytest.raises(ValidationError):
            ReportRequest(
                survey_id="test-survey",
                report_type="invalid_type",  # Invalid enum value
                format=ReportFormat.JSON
            )

    def test_invalid_report_format_validation(self):
        """Test validation with invalid report format."""
        with pytest.raises(ValidationError):
            ReportRequest(
                survey_id="test-survey",
                report_type=ReportType.SUMMARY,
                format="invalid_format"  # Invalid enum value
            )
