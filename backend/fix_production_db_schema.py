"""
Check and fix production database schema.
This script connects to Cloud SQL and ensures the platform_id column exists.
"""

import os
import sys
import asyncio
import asyncpg
from google.cloud import secretmanager

# GCP Configuration
PROJECT_ID = "survey-bot-detection"
INSTANCE_NAME = "bot-db"
DATABASE_NAME = "bot_detection"
REGION = "northamerica-northeast2"

# Cloud SQL connection string format
# postgresql+asyncpg://user:password@/database?host=/cloudsql/project:region:instance


async def get_database_url():
    """Get database URL from Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        secret_name = f"projects/{PROJECT_ID}/secrets/DATABASE_URL/versions/latest"
        response = client.access_secret_version(request={"name": secret_name})
        database_url = response.payload.data.decode("UTF-8")
        
        # Convert to asyncpg format (remove +asyncpg)
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        
        # For Cloud SQL, we need to use Unix socket or Cloud SQL Proxy
        # The connection string should use the Cloud SQL socket path
        if "cloudsql" not in database_url and "@localhost" not in database_url:
            # Extract connection details
            # Format: postgresql://user:password@host:port/database
            # For Cloud SQL via Unix socket: postgresql://user:password@/database?host=/cloudsql/project:region:instance
            print("[INFO] Database URL format detected. Will use Cloud SQL connection.")
        
        return database_url
    except Exception as e:
        print(f"[ERROR] Failed to get database URL from Secret Manager: {e}")
        return None


async def check_and_fix_schema():
    """Check and fix database schema."""
    print("=" * 60)
    print("Checking Production Database Schema")
    print("=" * 60)
    print()
    
    # Get database URL
    db_url = await get_database_url()
    if not db_url:
        print("[FAIL] Could not retrieve database URL")
        return False
    
    print(f"[INFO] Connecting to database: {DATABASE_NAME}")
    print()
    
    try:
        # For Cloud SQL, we need to use the Unix socket path
        # The connection string from Secret Manager should already have this
        # But if not, we'll construct it
        
        # Try to connect
        # Note: For Cloud SQL, you typically need Cloud SQL Proxy running
        # Or use the Unix socket path: /cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
        
        # Extract connection details from URL
        # For now, let's assume the URL is in the correct format
        
        # Connect to database
        conn = await asyncpg.connect(db_url)
        print("[PASS] Connected to database")
        
        # Check if platform_id column exists
        check_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'sessions' AND column_name = 'platform_id'
        """
        result = await conn.fetch(check_query)
        
        if result:
            print("[INFO] platform_id column already exists")
            await conn.close()
            return True
        
        # Add the column
        print("[INFO] Adding platform_id column...")
        await conn.execute("""
            ALTER TABLE sessions 
            ADD COLUMN platform_id VARCHAR(50)
        """)
        print("[PASS] Column added successfully")
        
        # Populate from existing platform values
        print("[INFO] Populating platform_id from existing platform values...")
        result = await conn.execute("""
            UPDATE sessions 
            SET platform_id = platform 
            WHERE platform IS NOT NULL AND platform_id IS NULL
        """)
        print(f"[PASS] Populated platform_id for existing records")
        
        await conn.close()
        
        print()
        print("=" * 60)
        print("[SUCCESS] Database schema migration completed!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print("[FAIL] Database migration failed!")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("This script requires Cloud SQL Proxy to be running, or")
        print("you can run the SQL manually in Cloud SQL Console:")
        print()
        print("SQL to run:")
        print("-" * 60)
        print("""
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'sessions' 
        AND column_name = 'platform_id'
    ) THEN
        ALTER TABLE sessions ADD COLUMN platform_id VARCHAR(50);
        
        UPDATE sessions 
        SET platform_id = platform 
        WHERE platform IS NOT NULL AND platform_id IS NULL;
        
        RAISE NOTICE 'platform_id column added successfully';
    ELSE
        RAISE NOTICE 'platform_id column already exists';
    END IF;
END $$;
        """)
        print("-" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print()
    print("Production Database Schema Migration")
    print("=" * 60)
    print()
    print("This script will:")
    print("1. Connect to production Cloud SQL database")
    print("2. Check if platform_id column exists")
    print("3. Add it if missing")
    print()
    print("Note: This requires Cloud SQL Proxy to be running, or")
    print("      you can run the SQL manually in Cloud SQL Console")
    print()
    
    result = asyncio.run(check_and_fix_schema())
    sys.exit(0 if result else 1)
