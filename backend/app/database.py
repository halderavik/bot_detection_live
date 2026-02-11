"""
Database configuration and session management.

This module sets up SQLAlchemy with async support for PostgreSQL,
including engine configuration, session management, and base model.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    poolclass=NullPool,   # Disable connection pooling for async
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Create base class for models
Base = declarative_base()

async def get_db() -> AsyncSession:
    """
    Dependency to get database session.
    
    Yields:
        AsyncSession: Database session for dependency injection.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        # Import all models to ensure they're registered with SQLAlchemy
        from app.models import (
            Session, BehaviorData, DetectionResult,
            SurveyQuestion, SurveyResponse, FraudIndicator,
            GridResponse, TimingAnalysis
        )
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
        logger.info("Tables created: sessions, behavior_data, detection_results, survey_questions, survey_responses, fraud_indicators, grid_responses, timing_analysis")

async def close_db():
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed") 