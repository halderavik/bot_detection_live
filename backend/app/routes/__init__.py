"""
Routes package.

This package contains the main API router and route configuration.
"""

from fastapi import APIRouter
from app.controllers.detection_controller import DetectionController
from app.controllers.dashboard_controller import DashboardController
from app.controllers.integration_controller import IntegrationController

# Create main API router
api_router = APIRouter()

# Include controller routers
detection_controller = DetectionController()
dashboard_controller = DashboardController()
integration_controller = IntegrationController()

api_router.include_router(detection_controller.get_router())
api_router.include_router(dashboard_controller.get_router())
api_router.include_router(integration_controller.get_router()) 