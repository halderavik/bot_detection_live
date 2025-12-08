"""
Migration script to add platform_id column and indexes to sessions table.

This migration:
1. Adds platform_id column to sessions table
2. Populates platform_id from existing platform values
3. Creates composite indexes for efficient hierarchical queries

Run this script manually or via database migration tool.
"""

import asyncio
import sys
import os
from sqlalchemy import text
from app.database import engine
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Ensure we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

async def run_migration():
    """Run the migration to add platform_id and indexes."""
    try:
        async with engine.begin() as conn:
            # Check if platform_id column already exists
            check_column = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='sessions' AND column_name='platform_id'
            """)
            result = await conn.execute(check_column)
            column_exists = result.scalar() is not None
            
            if not column_exists:
                logger.info("Adding platform_id column to sessions table...")
                # Add platform_id column
                await conn.execute(text("""
                    ALTER TABLE sessions 
                    ADD COLUMN platform_id VARCHAR(255)
                """))
                logger.info("platform_id column added successfully")
                
                # Populate platform_id from existing platform values
                logger.info("Populating platform_id from existing platform values...")
                await conn.execute(text("""
                    UPDATE sessions 
                    SET platform_id = platform 
                    WHERE platform IS NOT NULL AND platform_id IS NULL
                """))
                logger.info("platform_id populated from platform values")
            else:
                logger.info("platform_id column already exists, skipping creation")
            
            # Create indexes (using IF NOT EXISTS equivalent)
            logger.info("Creating composite indexes...")
            
            # Check and create hierarchical index
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent_session 
                ON sessions (survey_id, platform_id, respondent_id, id)
            """))
            
            # Check and create survey-platform index
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_survey_platform 
                ON sessions (survey_id, platform_id)
            """))
            
            # Check and create survey-platform-respondent index
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent 
                ON sessions (survey_id, platform_id, respondent_id)
            """))
            
            # Create individual indexes if they don't exist
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sessions_survey_id 
                ON sessions (survey_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sessions_platform_id 
                ON sessions (platform_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sessions_respondent_id 
                ON sessions (respondent_id)
            """))
            
            logger.info("All indexes created successfully")
            logger.info("Migration completed successfully")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_migration())

