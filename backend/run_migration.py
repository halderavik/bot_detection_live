"""
Direct migration runner for production database.
This script connects to Cloud SQL and runs the platform_id migration.
"""

import asyncio
import os
import sys
from sqlalchemy import text
from app.database import engine
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

async def run_migration():
    """Run the migration to add platform_id and indexes."""
    try:
        logger.info("Starting migration...")
        logger.info(f"Database URL: {os.getenv('DATABASE_URL', 'Not set')[:50]}...")
        
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
                    ADD COLUMN platform_id VARCHAR(50)
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
            
            # Create indexes
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
            logger.info("✅ Migration completed successfully")
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    asyncio.run(run_migration())

