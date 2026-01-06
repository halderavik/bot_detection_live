"""
Unified migration script to fix platform_id column differences between local and production.

This script:
1. Checks if platform_id column exists
2. Adds it if missing (VARCHAR(255) to match model)
3. Updates column type if it's VARCHAR(50) to VARCHAR(255)
4. Populates platform_id from existing platform values
5. Creates all necessary indexes

Works with both local and production databases via DATABASE_URL.
"""

import os
import sys
import asyncio

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import text, inspect
from app.database import engine
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

async def check_column_type(conn):
    """Check the current type of platform_id column if it exists."""
    check_type_query = text("""
        SELECT data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'sessions' AND column_name = 'platform_id'
    """)
    result = await conn.execute(check_type_query)
    row = result.fetchone()
    if row:
        return row[0], row[1]  # data_type, max_length
    return None, None

async def run_migration():
    """Run the migration to fix platform_id column."""
    try:
        logger.info("=" * 60)
        logger.info("Starting platform_id migration")
        logger.info("=" * 60)
        
        database_url = os.getenv('DATABASE_URL', '')
        if database_url:
            # Mask password in log
            masked_url = database_url.split('@')[-1] if '@' in database_url else database_url[:50]
            logger.info(f"Database: {masked_url}")
        
        async with engine.begin() as conn:
            # Check if platform_id column exists
            check_column = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='sessions' AND column_name='platform_id'
            """)
            result = await conn.execute(check_column)
            column_exists = result.scalar() is not None
            
            if not column_exists:
                logger.info("❌ platform_id column does not exist")
                logger.info("Adding platform_id column (VARCHAR(255))...")
                
                # Add platform_id column with correct type
                await conn.execute(text("""
                    ALTER TABLE sessions 
                    ADD COLUMN platform_id VARCHAR(255)
                """))
                logger.info("✅ platform_id column added successfully")
                
                # Populate platform_id from existing platform values
                logger.info("Populating platform_id from existing platform values...")
                update_result = await conn.execute(text("""
                    UPDATE sessions 
                    SET platform_id = platform 
                    WHERE platform IS NOT NULL AND platform_id IS NULL
                """))
                rows_updated = update_result.rowcount
                logger.info(f"✅ Populated platform_id for {rows_updated} existing records")
                
            else:
                logger.info("✅ platform_id column already exists")
                
                # Check column type
                data_type, max_length = await check_column_type(conn)
                logger.info(f"Current column type: {data_type}({max_length})")
                
                if max_length and max_length < 255:
                    logger.info(f"⚠️  Column type is {data_type}({max_length}), updating to VARCHAR(255)...")
                    # For PostgreSQL, we need to alter the column type
                    try:
                        await conn.execute(text("""
                            ALTER TABLE sessions 
                            ALTER COLUMN platform_id TYPE VARCHAR(255)
                        """))
                        logger.info("✅ Column type updated to VARCHAR(255)")
                    except Exception as e:
                        logger.warning(f"Could not update column type: {e}")
                        logger.info("This is okay if the column is already large enough")
                
                # Ensure all NULL platform_id values are populated from platform
                logger.info("Checking for NULL platform_id values...")
                update_result = await conn.execute(text("""
                    UPDATE sessions 
                    SET platform_id = platform 
                    WHERE platform IS NOT NULL AND platform_id IS NULL
                """))
                rows_updated = update_result.rowcount
                if rows_updated > 0:
                    logger.info(f"✅ Populated platform_id for {rows_updated} additional records")
                else:
                    logger.info("✅ All platform_id values are already populated")
            
            # Create indexes
            logger.info("Creating composite indexes...")
            
            indexes = [
                ("idx_survey_platform_respondent_session", 
                 "CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent_session ON sessions (survey_id, platform_id, respondent_id, id)"),
                ("idx_survey_platform", 
                 "CREATE INDEX IF NOT EXISTS idx_survey_platform ON sessions (survey_id, platform_id)"),
                ("idx_survey_platform_respondent", 
                 "CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent ON sessions (survey_id, platform_id, respondent_id)"),
                ("idx_sessions_platform_id", 
                 "CREATE INDEX IF NOT EXISTS idx_sessions_platform_id ON sessions (platform_id)"),
            ]
            
            for index_name, index_sql in indexes:
                try:
                    await conn.execute(text(index_sql))
                    logger.info(f"✅ Created/verified index: {index_name}")
                except Exception as e:
                    logger.warning(f"⚠️  Index {index_name} creation issue: {e}")
            
            logger.info("=" * 60)
            logger.info("✅ Migration completed successfully!")
            logger.info("=" * 60)
            
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ Migration failed: {e}")
        logger.error("=" * 60)
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    asyncio.run(run_migration())
