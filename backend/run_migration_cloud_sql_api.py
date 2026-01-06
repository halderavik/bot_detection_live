"""
Run database migration using Cloud SQL Admin API.
This script uses the Google Cloud SQL Admin API to execute SQL directly.
"""

import os
import sys
from google.cloud import sqladmin_v1
from google.oauth2 import service_account
import json

def get_project_id():
    """Get project ID from environment or default."""
    return os.getenv('GCP_PROJECT_ID', 'survey-bot-detection')

def run_migration_via_api():
    """Run migration using Cloud SQL Admin API."""
    project_id = get_project_id()
    instance_name = "bot-db"
    database_name = "bot_detection"
    
    print(f"Running migration via Cloud SQL Admin API...")
    print(f"Project: {project_id}")
    print(f"Instance: {instance_name}")
    print(f"Database: {database_name}")
    print()
    
    # SQL migration script
    migration_sql = """
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
"""
    
    try:
        # Initialize the Cloud SQL Admin client
        client = sqladmin_v1.SqlInstancesServiceClient()
        
        # Note: The Cloud SQL Admin API doesn't have a direct execute-sql method
        # We need to use the databases.executeSql method which requires authentication
        # and proper IAM permissions
        
        print("Note: Cloud SQL Admin API requires specific setup.")
        print("Alternative: Use Cloud SQL Console or gcloud sql connect")
        print()
        print("SQL to execute:")
        print(migration_sql)
        print()
        print("To run manually:")
        print("1. Go to: https://console.cloud.google.com/sql/instances/bot-db/databases/bot_detection")
        print("2. Click 'Open Cloud Shell' or use Query tab")
        print("3. Paste and run the SQL above")
        
        # Actually, let's try using the REST API directly
        import subprocess
        import tempfile
        
        # Save SQL to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write(migration_sql)
            temp_file = f.name
        
        print()
        print(f"SQL saved to: {temp_file}")
        print()
        print("Attempting via gcloud sql connect (interactive)...")
        print("Run this command:")
        print(f"gcloud sql connect {instance_name} --user=bot_user --database={database_name} --project={project_id}")
        print("Then in psql, run:")
        print(f"\\i {temp_file}")
        
        return False  # Indicate manual execution needed
        
    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Please run the migration manually via Cloud SQL Console")
        return False

if __name__ == "__main__":
    success = run_migration_via_api()
    sys.exit(0 if success else 1)
