"""
Main FastAPI application entry point for Bot Detection API.

This module initializes the FastAPI application with all necessary middleware,
routers, and configuration for the bot detection service.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.utils.rate_limit import RateLimitMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.config import settings
from app.database import engine, Base
from app.routes import api_router
from app.utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Bot Detection API...")
    
    # Data-centre IP ranges load in the background; nothing waits for them.
    import asyncio
    from app.utils import ip_intel
    ranges_task = asyncio.create_task(ip_intel.keep_fresh())

    # Create database tables (with error handling)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        logger.warning("Application will start without database tables")

    # Indexes the per-respondent queries need, built in the background (see app/db_indexes.py).
    from app.db_indexes import ensure_indexes
    indexes_task = asyncio.create_task(ensure_indexes(engine))

    # Settings saved on the Settings page override the environment; re-read every 30 s.
    from app.database import AsyncSessionLocal
    from app.services import runtime_settings
    from app.services.openai_service import openai_service
    runtime_settings.on_change(openai_service.reload)
    try:
        async with AsyncSessionLocal() as db:
            await runtime_settings.load(db)
    except Exception as e:
        logger.warning(f"Saved settings were not loaded: {e}")
    settings_task = asyncio.create_task(runtime_settings.keep_fresh(AsyncSessionLocal))
    
    yield
    ranges_task.cancel()
    settings_task.cancel()
    indexes_task.cancel()
    
    # Shutdown
    logger.info("Shutting down Bot Detection API...")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Bot Detection API",
        description="Advanced bot detection service with behavioral analysis",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins for now
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        # Reason: the live quality data merge returns its report in a header the browser must read.
        expose_headers=["Content-Disposition", "X-Quality-Report"],
    )
    
    app.add_middleware(RateLimitMiddleware)

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )
    
    # Include routers
    app.include_router(api_router, prefix="/api/v1")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint for monitoring."""
        from app.utils import ip_intel

        return {"status": "healthy", "service": "bot-detection-api", "datacenter_networks": ip_intel.loaded()}
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
        if not settings.ENABLE_METRICS:
            raise HTTPException(status_code=404, detail="Metrics endpoint disabled")
        
        from fastapi import Response
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "Bot Detection API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    ) 