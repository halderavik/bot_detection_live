"""
Pydantic models for report builder functionality.

This module defines the request and response models for generating
survey reports including summary and detailed respondent data.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class ReportType(str, Enum):
    """Report type enumeration."""
    SUMMARY = "summary"
    DETAILED = "detailed"

class ReportFormat(str, Enum):
    """Report format enumeration."""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"

class SurveySummaryReport(BaseModel):
    """Survey summary report model."""
    
    survey_id: str = Field(..., description="Survey identifier")
    survey_name: Optional[str] = Field(None, description="Survey name if available")
    total_respondents: int = Field(..., description="Total number of respondents")
    total_sessions: int = Field(..., description="Total number of sessions")
    bot_detections: int = Field(..., description="Number of bot detections")
    human_respondents: int = Field(..., description="Number of human respondents")
    bot_detection_rate: float = Field(..., description="Bot detection rate as percentage")
    
    # Activity distribution
    activity_distribution: Dict[str, int] = Field(..., description="Distribution of activity types")
    
    # Risk level distribution
    risk_distribution: Dict[str, int] = Field(..., description="Distribution of risk levels")
    
    # Platform information
    platform: Optional[str] = Field(None, description="Survey platform")
    
    # Time range
    date_range: Dict[str, Optional[str]] = Field(..., description="Date range of the data")
    
    # Additional metadata
    average_session_duration: Optional[float] = Field(None, description="Average session duration in minutes")
    average_events_per_session: Optional[float] = Field(None, description="Average events per session")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

class RespondentDetail(BaseModel):
    """Individual respondent detail for detailed reports."""
    
    session_id: str = Field(..., description="Session identifier")
    respondent_id: Optional[str] = Field(None, description="Respondent identifier")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity time")
    
    # Detection results
    is_bot: bool = Field(..., description="Bot detection result")
    confidence_score: float = Field(..., description="Confidence score (0.0-1.0)")
    risk_level: str = Field(..., description="Risk level classification")
    
    # Activity metrics
    total_events: int = Field(..., description="Total number of events")
    session_duration_minutes: float = Field(..., description="Session duration in minutes")
    
    # Event type breakdown
    event_breakdown: Dict[str, int] = Field(..., description="Breakdown of event types")
    
    # Detection method scores
    method_scores: Dict[str, float] = Field(..., description="Individual method scores")
    
    # Flagged patterns
    flagged_patterns: Optional[Dict[str, Any]] = Field(None, description="Flagged behavioral patterns")
    
    # Analysis summary
    analysis_summary: Optional[str] = Field(None, description="Human-readable analysis summary")
    
    # Bot detection explanation
    bot_explanation: Optional[str] = Field(None, description="Explanation if detected as bot")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

class DetailedReport(BaseModel):
    """Detailed report model with all respondents."""
    
    survey_id: str = Field(..., description="Survey identifier")
    survey_name: Optional[str] = Field(None, description="Survey name if available")
    total_respondents: int = Field(..., description="Total number of respondents")
    generated_at: datetime = Field(..., description="Report generation timestamp")
    
    # Summary statistics
    summary_stats: Dict[str, Any] = Field(..., description="Summary statistics")
    
    # Individual respondent details
    respondents: List[RespondentDetail] = Field(..., description="List of respondent details")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

class ReportRequest(BaseModel):
    """Report generation request model."""
    
    survey_id: str = Field(..., description="Survey identifier to generate report for")
    report_type: ReportType = Field(..., description="Type of report to generate")
    format: ReportFormat = Field(ReportFormat.JSON, description="Output format")
    include_inactive: bool = Field(False, description="Include inactive sessions")
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")

class ReportResponse(BaseModel):
    """Report generation response model."""
    
    success: bool = Field(..., description="Whether report generation was successful")
    report_id: Optional[str] = Field(None, description="Unique report identifier")
    report_type: ReportType = Field(..., description="Type of report generated")
    format: ReportFormat = Field(..., description="Output format")
    generated_at: datetime = Field(..., description="Report generation timestamp")
    
    # For summary reports
    summary_data: Optional[SurveySummaryReport] = Field(None, description="Summary report data")
    
    # For detailed reports
    detailed_data: Optional[DetailedReport] = Field(None, description="Detailed report data")
    
    # Download information
    download_url: Optional[str] = Field(None, description="URL to download the report file")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    
    # Error information
    error_message: Optional[str] = Field(None, description="Error message if generation failed")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

class SurveyListResponse(BaseModel):
    """Response model for available surveys."""
    
    surveys: List[Dict[str, Any]] = Field(..., description="List of available surveys")
    total_count: int = Field(..., description="Total number of surveys")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
