"""
Main API router for the Bot Detection API.

This module combines all controller routes into a single router
for the FastAPI application.
"""

from fastapi import APIRouter

from controllers.detection_controller import router as detection_router
from controllers.dashboard_controller import router as dashboard_router
from controllers.integration_controller import router as integration_router

# Create main router
router = APIRouter()

# Include all controller routers
router.include_router(detection_router)
router.include_router(dashboard_router)
router.include_router(integration_router) 