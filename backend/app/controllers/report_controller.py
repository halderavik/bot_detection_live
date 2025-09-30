"""
Report Controller.

This controller handles report generation endpoints for survey reports
including summary statistics and detailed respondent data with CSV export.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import io

from app.database import get_db
from app.services.report_service import ReportService
from app.models.report_models import (
    ReportRequest, ReportResponse, ReportType, ReportFormat,
    SurveyListResponse
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class ReportController:
    """Controller for report generation endpoints."""
    
    def __init__(self):
        """Initialize the report controller."""
        self.router = APIRouter(prefix="/reports", tags=["reports"])
        self.report_service = ReportService()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes for report endpoints."""
        
        @self.router.get("/surveys", response_model=SurveyListResponse)
        async def get_available_surveys(
            db: AsyncSession = Depends(get_db)
        ):
            """Get list of available surveys for report generation."""
            try:
                surveys = await self.report_service.get_available_surveys(db)
                
                return SurveyListResponse(
                    surveys=surveys,
                    total_count=len(surveys)
                )
                
            except Exception as e:
                logger.error(f"Error getting available surveys: {e}")
                raise HTTPException(status_code=500, detail="Failed to get available surveys")
        
        @self.router.post("/generate", response_model=ReportResponse)
        async def generate_report(
            request: ReportRequest,
            db: AsyncSession = Depends(get_db)
        ):
            """Generate a report for a specific survey."""
            try:
                response = await self.report_service.generate_report(request, db)
                
                if not response.success:
                    raise HTTPException(status_code=400, detail=response.error_message)
                
                return response
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error generating report: {e}")
                raise HTTPException(status_code=500, detail="Failed to generate report")
        
        @self.router.get("/summary/{survey_id}")
        async def get_summary_report(
            survey_id: str,
            db: AsyncSession = Depends(get_db),
            include_inactive: bool = Query(False, description="Include inactive sessions"),
            date_from: Optional[datetime] = Query(None, description="Start date filter"),
            date_to: Optional[datetime] = Query(None, description="End date filter")
        ):
            """Get a summary report for a specific survey."""
            try:
                summary_report = await self.report_service.generate_summary_report(
                    survey_id=survey_id,
                    db=db,
                    date_from=date_from,
                    date_to=date_to,
                    include_inactive=include_inactive
                )
                
                return summary_report
                
            except Exception as e:
                logger.error(f"Error getting summary report: {e}")
                raise HTTPException(status_code=500, detail="Failed to get summary report")
        
        @self.router.get("/detailed/{survey_id}")
        async def get_detailed_report(
            survey_id: str,
            db: AsyncSession = Depends(get_db),
            include_inactive: bool = Query(False, description="Include inactive sessions"),
            date_from: Optional[datetime] = Query(None, description="Start date filter"),
            date_to: Optional[datetime] = Query(None, description="End date filter")
        ):
            """Get a detailed report for a specific survey."""
            try:
                detailed_report = await self.report_service.generate_detailed_report(
                    survey_id=survey_id,
                    db=db,
                    date_from=date_from,
                    date_to=date_to,
                    include_inactive=include_inactive
                )
                
                return detailed_report
                
            except Exception as e:
                logger.error(f"Error getting detailed report: {e}")
                raise HTTPException(status_code=500, detail="Failed to get detailed report")
        
        @self.router.get("/detailed/{survey_id}/csv")
        async def download_detailed_report_csv(
            survey_id: str,
            db: AsyncSession = Depends(get_db),
            include_inactive: bool = Query(False, description="Include inactive sessions"),
            date_from: Optional[datetime] = Query(None, description="Start date filter"),
            date_to: Optional[datetime] = Query(None, description="End date filter")
        ):
            """Download detailed report as CSV file."""
            try:
                # Generate detailed report
                detailed_report = await self.report_service.generate_detailed_report(
                    survey_id=survey_id,
                    db=db,
                    date_from=date_from,
                    date_to=date_to,
                    include_inactive=include_inactive
                )
                
                # Generate CSV content
                csv_content = self.report_service.generate_csv_report(detailed_report)
                
                # Create streaming response
                csv_io = io.StringIO(csv_content)
                
                def generate_csv():
                    yield from csv_io
                
                # Generate filename with timestamp
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"survey_{survey_id}_detailed_report_{timestamp}.csv"
                
                return StreamingResponse(
                    generate_csv(),
                    media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )
                
            except Exception as e:
                logger.error(f"Error downloading CSV report: {e}")
                raise HTTPException(status_code=500, detail="Failed to download CSV report")
        
        @self.router.get("/summary/{survey_id}/pdf")
        async def download_summary_report_pdf(
            survey_id: str,
            db: AsyncSession = Depends(get_db),
            include_inactive: bool = Query(False, description="Include inactive sessions"),
            date_from: Optional[datetime] = Query(None, description="Start date filter"),
            date_to: Optional[datetime] = Query(None, description="End date filter")
        ):
            """Download summary report as PDF file."""
            try:
                # Generate summary report
                summary_report = await self.report_service.generate_summary_report(
                    survey_id=survey_id,
                    db=db,
                    date_from=date_from,
                    date_to=date_to,
                    include_inactive=include_inactive
                )
                
                # For now, return JSON data
                # In a real implementation, you'd generate a PDF using a library like reportlab
                # and return it as a streaming response
                
                return {
                    "message": "PDF generation not yet implemented",
                    "data": summary_report,
                    "note": "Use the JSON endpoint for now, PDF generation will be added in future version"
                }
                
            except Exception as e:
                logger.error(f"Error downloading PDF report: {e}")
                raise HTTPException(status_code=500, detail="Failed to download PDF report")
    
    def get_router(self) -> APIRouter:
        """Get the router for this controller."""
        return self.router
