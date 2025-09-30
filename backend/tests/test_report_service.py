"""
Tests for the report service functionality.

This module contains unit tests for the report generation service
including summary and detailed report generation.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.report_service import ReportService
from app.models import Session, BehaviorData, DetectionResult
from app.models.report_models import ReportRequest, ReportType, ReportFormat


class TestReportService:
    """Test cases for the ReportService class."""
    
    @pytest.fixture
    def report_service(self):
        """Create a ReportService instance for testing."""
        return ReportService()
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def sample_sessions(self):
        """Create sample session data for testing."""
        sessions = []
        
        # Create a sample session with bot detection
        session1 = MagicMock(spec=Session)
        session1.id = "session-1"
        session1.survey_id = "SV_123456"
        session1.platform = "qualtrics"
        session1.respondent_id = "R_789012"
        session1.created_at = datetime.utcnow() - timedelta(hours=2)
        session1.last_activity = datetime.utcnow() - timedelta(hours=1)
        session1.is_active = True
        session1.is_completed = True
        
        # Mock behavior data
        behavior_data1 = MagicMock(spec=BehaviorData)
        behavior_data1.event_type = "keystroke"
        behavior_data1.timestamp = datetime.utcnow() - timedelta(hours=1, minutes=30)
        session1.behavior_data = [behavior_data1, behavior_data1, behavior_data1]  # 3 events
        
        # Mock detection result
        detection1 = MagicMock(spec=DetectionResult)
        detection1.is_bot = True
        detection1.confidence_score = 0.85
        detection1.risk_level = "high"
        detection1.method_scores = {"keystroke_analysis": 0.8, "mouse_analysis": 0.7}
        detection1.flagged_patterns = {"rapid_typing": {"count": 5, "severity": "high"}}
        detection1.analysis_summary = "Bot detected due to rapid typing patterns"
        detection1.created_at = datetime.utcnow() - timedelta(minutes=30)
        session1.detection_results = [detection1]
        
        sessions.append(session1)
        
        # Create a sample session with human detection
        session2 = MagicMock(spec=Session)
        session2.id = "session-2"
        session2.survey_id = "SV_123456"
        session2.platform = "qualtrics"
        session2.respondent_id = "R_789013"
        session2.created_at = datetime.utcnow() - timedelta(hours=1)
        session2.last_activity = datetime.utcnow() - timedelta(minutes=30)
        session2.is_active = True
        session2.is_completed = True
        
        # Mock behavior data
        behavior_data2 = MagicMock(spec=BehaviorData)
        behavior_data2.event_type = "click"
        behavior_data2.timestamp = datetime.utcnow() - timedelta(minutes=45)
        session2.behavior_data = [behavior_data2, behavior_data2]  # 2 events
        
        # Mock detection result
        detection2 = MagicMock(spec=DetectionResult)
        detection2.is_bot = False
        detection2.confidence_score = 0.75
        detection2.risk_level = "low"
        detection2.method_scores = {"keystroke_analysis": 0.2, "mouse_analysis": 0.1}
        detection2.flagged_patterns = None
        detection2.analysis_summary = "Human behavior detected"
        detection2.created_at = datetime.utcnow() - timedelta(minutes=15)
        session2.detection_results = [detection2]
        
        sessions.append(session2)
        
        return sessions
    
    @pytest.mark.asyncio
    async def test_get_available_surveys(self, report_service, mock_db):
        """Test getting available surveys."""
        # Mock database query result
        mock_result = MagicMock()
        mock_result.survey_id = "SV_123456"
        mock_result.platform = "qualtrics"
        mock_result.session_count = 10
        mock_result.first_session = datetime.utcnow() - timedelta(days=7)
        mock_result.last_session = datetime.utcnow()
        
        # Mock the execute method to return different results for different calls
        mock_db.execute.side_effect = [
            [mock_result],  # First call for survey query
            MagicMock(scalar=MagicMock(return_value=2))  # Second call for bot count
        ]
        
        surveys = await report_service.get_available_surveys(mock_db)
        
        assert len(surveys) == 1
        assert surveys[0]["survey_id"] == "SV_123456"
        assert surveys[0]["platform"] == "qualtrics"
        assert surveys[0]["session_count"] == 10
        assert surveys[0]["bot_count"] == 2
        assert surveys[0]["human_count"] == 8
        assert surveys[0]["bot_rate"] == 20.0
    
    @pytest.mark.asyncio
    async def test_generate_summary_report(self, report_service, mock_db, sample_sessions):
        """Test generating a summary report."""
        # Mock database query to return sample sessions
        mock_session_result = MagicMock()
        mock_session_result.scalars.return_value.all.return_value = sample_sessions
        
        # Mock detection query
        mock_detection_result = MagicMock()
        mock_detection_result.scalars.return_value.all.return_value = [
            session.detection_results[0] for session in sample_sessions
        ]
        
        # Mock activity query
        mock_activity_result = MagicMock()
        mock_activity_result.all.return_value = [("keystroke", 3), ("click", 2)]
        
        # Mock event count queries
        mock_event_count_result = MagicMock()
        mock_event_count_result.scalar.return_value = 3  # For first session
        mock_event_count_result2 = MagicMock()
        mock_event_count_result2.scalar.return_value = 2  # For second session
        
        # Set up side effects for multiple execute calls
        mock_db.execute.side_effect = [
            mock_session_result,  # Session query
            mock_detection_result,  # Detection query
            mock_activity_result,  # Activity query
            mock_event_count_result,  # Event count for session 1
            mock_event_count_result2,  # Event count for session 2
        ]
        
        summary_report = await report_service.generate_summary_report(
            "SV_123456", mock_db
        )
        
        assert summary_report.survey_id == "SV_123456"
        assert summary_report.total_respondents == 2
        assert summary_report.total_sessions == 2
        assert summary_report.bot_detections == 1
        assert summary_report.human_respondents == 1
        assert summary_report.bot_detection_rate == 50.0
        assert summary_report.platform == "qualtrics"
        assert "keystroke" in summary_report.activity_distribution
        assert "click" in summary_report.activity_distribution
        assert "high" in summary_report.risk_distribution
        assert "low" in summary_report.risk_distribution
    
    @pytest.mark.asyncio
    async def test_generate_detailed_report(self, report_service, mock_db, sample_sessions):
        """Test generating a detailed report."""
        # Mock database query to return sample sessions
        mock_session_result = MagicMock()
        mock_session_result.scalars.return_value.all.return_value = sample_sessions
        mock_db.execute.return_value = mock_session_result
        
        detailed_report = await report_service.generate_detailed_report(
            "SV_123456", mock_db
        )
        
        assert detailed_report.survey_id == "SV_123456"
        assert detailed_report.total_respondents == 2
        assert len(detailed_report.respondents) == 2
        assert detailed_report.generated_at is not None
        
        # Check first respondent (bot)
        bot_respondent = detailed_report.respondents[0]
        assert bot_respondent.is_bot is True
        assert bot_respondent.confidence_score == 0.85
        assert bot_respondent.risk_level == "high"
        assert bot_respondent.total_events == 3
        assert bot_respondent.bot_explanation is not None
        
        # Check second respondent (human)
        human_respondent = detailed_report.respondents[1]
        assert human_respondent.is_bot is False
        assert human_respondent.confidence_score == 0.75
        assert human_respondent.risk_level == "low"
        assert human_respondent.total_events == 2
    
    def test_generate_csv_report(self, report_service, sample_sessions):
        """Test generating CSV content from detailed report."""
        # Create a mock detailed report
        from app.models.report_models import DetailedReport, RespondentDetail
        
        respondents = []
        for session in sample_sessions:
            respondent = RespondentDetail(
                session_id=session.id,
                respondent_id=session.respondent_id,
                created_at=session.created_at,
                last_activity=session.last_activity,
                is_bot=session.detection_results[0].is_bot,
                confidence_score=session.detection_results[0].confidence_score,
                risk_level=session.detection_results[0].risk_level,
                total_events=len(session.behavior_data),
                session_duration_minutes=60.0,
                event_breakdown={"keystroke": 3, "click": 2},
                method_scores=session.detection_results[0].method_scores,
                flagged_patterns=session.detection_results[0].flagged_patterns,
                analysis_summary=session.detection_results[0].analysis_summary,
                bot_explanation="Test explanation"
            )
            respondents.append(respondent)
        
        detailed_report = DetailedReport(
            survey_id="SV_123456",
            total_respondents=2,
            generated_at=datetime.utcnow(),
            summary_stats={"total_sessions": 2, "bot_detections": 1},
            respondents=respondents
        )
        
        csv_content = report_service.generate_csv_report(detailed_report)
        
        assert csv_content is not None
        assert "Session ID" in csv_content
        assert "Respondent ID" in csv_content
        assert "Is Bot" in csv_content
        assert "Confidence Score" in csv_content
        assert "session-1" in csv_content
        assert "session-2" in csv_content
        assert "Yes" in csv_content  # Bot detection
        assert "No" in csv_content   # Human detection
    
    def test_generate_bot_explanation(self, report_service):
        """Test generating bot explanation from detection result."""
        # Create a mock detection result
        detection = MagicMock(spec=DetectionResult)
        detection.flagged_patterns = {
            "rapid_typing": {"count": 5, "severity": "high"},
            "uniform_intervals": {"count": 3, "severity": "medium"}
        }
        detection.method_scores = {
            "keystroke_analysis": 0.9,
            "mouse_analysis": 0.8
        }
        detection.analysis_summary = "Bot behavior detected"
        
        explanation = report_service._generate_bot_explanation(detection)
        
        assert "rapid_typing" in explanation
        assert "uniform_intervals" in explanation
        assert "keystroke_analysis" in explanation
        assert "mouse_analysis" in explanation
        assert "Bot behavior detected" in explanation
    
    @pytest.mark.asyncio
    async def test_generate_report_summary(self, report_service, mock_db, sample_sessions):
        """Test generating a report with summary type."""
        # Mock database query to return sample sessions
        mock_session_result = MagicMock()
        mock_session_result.scalars.return_value.all.return_value = sample_sessions
        
        # Mock detection query
        mock_detection_result = MagicMock()
        mock_detection_result.scalars.return_value.all.return_value = [
            session.detection_results[0] for session in sample_sessions
        ]
        
        # Mock activity query
        mock_activity_result = MagicMock()
        mock_activity_result.all.return_value = [("keystroke", 3), ("click", 2)]
        
        # Mock event count queries
        mock_event_count_result = MagicMock()
        mock_event_count_result.scalar.return_value = 3  # For first session
        mock_event_count_result2 = MagicMock()
        mock_event_count_result2.scalar.return_value = 2  # For second session
        
        # Set up side effects for multiple execute calls
        mock_db.execute.side_effect = [
            mock_session_result,  # Session query
            mock_detection_result,  # Detection query
            mock_activity_result,  # Activity query
            mock_event_count_result,  # Event count for session 1
            mock_event_count_result2,  # Event count for session 2
        ]
        
        request = ReportRequest(
            survey_id="SV_123456",
            report_type=ReportType.SUMMARY,
            format=ReportFormat.JSON
        )
        
        response = await report_service.generate_report(request, mock_db)
        
        assert response.success is True
        assert response.report_type == ReportType.SUMMARY
        assert response.format == ReportFormat.JSON
        assert response.summary_data is not None
        assert response.summary_data.survey_id == "SV_123456"
        assert response.detailed_data is None
    
    @pytest.mark.asyncio
    async def test_generate_report_detailed(self, report_service, mock_db, sample_sessions):
        """Test generating a report with detailed type."""
        # Mock database query to return sample sessions
        mock_session_result = MagicMock()
        mock_session_result.scalars.return_value.all.return_value = sample_sessions
        mock_db.execute.return_value = mock_session_result
        
        request = ReportRequest(
            survey_id="SV_123456",
            report_type=ReportType.DETAILED,
            format=ReportFormat.CSV
        )
        
        response = await report_service.generate_report(request, mock_db)
        
        assert response.success is True
        assert response.report_type == ReportType.DETAILED
        assert response.format == ReportFormat.CSV
        assert response.detailed_data is not None
        assert response.detailed_data.survey_id == "SV_123456"
        assert response.summary_data is None
        assert response.file_size is not None
