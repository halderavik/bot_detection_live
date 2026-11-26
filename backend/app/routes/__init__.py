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
from app.controllers.fraud_detection_controller import FraudDetectionController
from app.controllers.text_analysis_controller import router as text_analysis_router
from app.controllers.survey_tracking_controller import router as survey_tracking_router
from app.controllers.live_quality_controller import router as live_quality_router
from app.controllers.settings_controller import router as settings_router

# Create main API router
api_router = APIRouter()

# Include controller routers
detection_controller = DetectionController()
dashboard_controller = DashboardController()
integration_controller = IntegrationController()
report_controller = ReportController()
hierarchical_controller = HierarchicalController()
fraud_detection_controller = FraudDetectionController()

api_router.include_router(detection_controller.get_router())
api_router.include_router(dashboard_controller.get_router())
api_router.include_router(integration_controller.get_router())
api_router.include_router(report_controller.get_router())
api_router.include_router(hierarchical_controller.get_router())  # New hierarchical endpoints
api_router.include_router(fraud_detection_controller.get_router())  # Fraud detection endpoints
api_router.include_router(text_analysis_router)
api_router.include_router(survey_tracking_router)  # Decipher XML upload: add live tracking
api_router.include_router(live_quality_router)  # Live quality: rules, results, exports, data merge
api_router.include_router(settings_router)  # Settings page: integration keys, tracking, bot threshold
