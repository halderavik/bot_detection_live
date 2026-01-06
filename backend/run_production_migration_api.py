"""
Run platform_id migration on production Cloud SQL using Cloud SQL Admin API.

This script uses the Google Cloud SQL Admin API to execute SQL directly
on the production database without requiring psql.
"""

import os
import sys
from google.cloud import sqladmin_v1
from google.auth import default
import json

# GCP Configuration
PROJECT_ID = "survey-bot-detection"
INSTANCE_NAME = "bot-db"
DATABASE_NAME = "bot_detection"
REGION = "northamerica-northeast2"

def run_migration_via_api():
    """Run migration using Cloud SQL Admin API."""
    print("=" * 60)
    print("Platform ID Migration for Production Cloud SQL")
    print("Using Cloud SQL Admin API")
    print("=" * 60)
    print(f"Project: {PROJECT_ID}")
    print(f"Instance: {INSTANCE_NAME}")
    print(f"Database: {DATABASE_NAME}")
    print("=" * 60)
    print()
    
    # Migration SQL
    migration_sql = """
DO $$
BEGIN
    -- Check if column exists
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'sessions' 
        AND column_name = 'platform_id'
    ) THEN
        -- Add platform_id column (VARCHAR(255) to match model)
        ALTER TABLE sessions 
        ADD COLUMN platform_id VARCHAR(255);
        
        RAISE NOTICE 'platform_id column added successfully';
    ELSE
        RAISE NOTICE 'platform_id column already exists';
    END IF;
END $$;

-- Populate platform_id from existing platform values
UPDATE sessions 
SET platform_id = platform 
WHERE platform IS NOT NULL AND platform_id IS NULL;

-- Create composite indexes
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent_session 
ON sessions (survey_id, platform_id, respondent_id, id);

CREATE INDEX IF NOT EXISTS idx_survey_platform 
ON sessions (survey_id, platform_id);

CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent 
ON sessions (survey_id, platform_id, respondent_id);

CREATE INDEX IF NOT EXISTS idx_sessions_platform_id 
ON sessions (platform_id);
"""
    
    try:
        # Get default credentials
        print("Authenticating with Google Cloud...")
        credentials, project = default()
        print(f"Authenticated with project: {project}")
        print()
        
        # Initialize the Cloud SQL Admin client
        print("Initializing Cloud SQL Admin API client...")
        client = sqladmin_v1.SqlInstancesServiceClient(credentials=credentials)
        
        # Note: The Cloud SQL Admin API doesn't have a direct execute-sql method
        # We need to use the REST API or another method
        # Let's use the REST API directly via requests
        
        print("Using REST API to execute SQL...")
        import requests
        from google.auth.transport.requests import Request
        
        # Get access token
        credentials.refresh(Request())
        access_token = credentials.token
        
        # Use the Cloud SQL Admin API REST endpoint
        # The API endpoint for executing SQL is:
        # POST https://sqladmin.googleapis.com/v1/projects/{project}/instances/{instance}/databases/{database}/executeSql
        
        api_url = f"https://sqladmin.googleapis.com/v1/projects/{PROJECT_ID}/instances/{INSTANCE_NAME}/databases/{DATABASE_NAME}/executeSql"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Split SQL into individual statements (Cloud SQL API requires one statement at a time)
        # For now, let's provide instructions for manual execution
        print()
        print("=" * 60)
        print("Cloud SQL Admin API requires manual SQL execution")
        print("=" * 60)
        print()
        print("The Cloud SQL Admin API doesn't support direct SQL execution")
        print("via the Python client library. Please use one of these methods:")
        print()
        print("OPTION 1: Cloud SQL Console (Recommended)")
        print(f"  1. Go to: https://console.cloud.google.com/sql/instances/{INSTANCE_NAME}")
        print(f"  2. Click on 'Databases' tab")
        print(f"  3. Select database: {DATABASE_NAME}")
        print("  4. Click 'Open Cloud Shell' or use Query tab")
        print("  5. Paste and run the SQL below")
        print()
        print("OPTION 2: Use gcloud with Cloud Shell")
        print("  1. Open Cloud Shell: https://shell.cloud.google.com/")
        print("  2. Run: gcloud sql connect bot-db --user=bot_user --database=bot_detection --project=survey-bot-detection")
        print("  3. In psql, paste the SQL below")
        print()
        print("=" * 60)
        print("Migration SQL:")
        print("=" * 60)
        print(migration_sql)
        print("=" * 60)
        print()
        
        # Save SQL to file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False, encoding='utf-8') as f:
            f.write(migration_sql)
            temp_file = f.name
        
        print(f"SQL saved to: {temp_file}")
        print()
        
        return False  # Indicate manual execution needed
        
    except ImportError as e:
        print(f"ERROR: Missing required library: {e}")
        print("Please install: pip install google-cloud-sql-admin")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration_via_api()
    sys.exit(0 if success else 1)
