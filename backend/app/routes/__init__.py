"""
Routes package.

This package contains the main API router and route configuration.
"""

from fastapi import APIRouter
from app.controllers.detection_controller import DetectionController
from app.controllers.dashboard_controller import DashboardController
from app.controllers.integration_controller import IntegrationController
from app.controllers.report_controller import ReportController
from app.controllers.hierarchical_controller import HierarchicalController
from app.controllers.text_analysis_controller import router as text_analysis_router

# Create main API router
api_router = APIRouter()

# Include controller routers
detection_controller = DetectionController()
dashboard_controller = DashboardController()
integration_controller = IntegrationController()
report_controller = ReportController()
hierarchical_controller = HierarchicalController()

api_router.include_router(detection_controller.get_router())
api_router.include_router(dashboard_controller.get_router())
api_router.include_router(integration_controller.get_router())
api_router.include_router(report_controller.get_router())
api_router.include_router(hierarchical_controller.get_router())  # New hierarchical endpoints
api_router.include_router(text_analysis_router) 