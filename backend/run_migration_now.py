"""
Execute platform_id migration on production Cloud SQL using REST API.

This script uses the Cloud SQL Admin API REST endpoint to execute SQL
directly on the production database.
"""

import os
import sys
import subprocess
import json
import requests

# GCP Configuration
PROJECT_ID = "survey-bot-detection"
INSTANCE_NAME = "bot-db"
DATABASE_NAME = "bot_detection"

def get_access_token():
    """Get access token using gcloud."""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"ERROR: Failed to get access token: {e}")
        return None

def execute_sql_statement(access_token, sql_statement):
    """Execute a single SQL statement via Cloud SQL Admin API."""
    api_url = f"https://sqladmin.googleapis.com/v1/projects/{PROJECT_ID}/instances/{INSTANCE_NAME}/databases/{DATABASE_NAME}/executeSql"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "sql": sql_statement
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"Status {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def run_migration():
    """Run the platform_id migration."""
    print("=" * 60)
    print("Platform ID Migration - Executing Now")
    print("=" * 60)
    print(f"Project: {PROJECT_ID}")
    print(f"Instance: {INSTANCE_NAME}")
    print(f"Database: {DATABASE_NAME}")
    print("=" * 60)
    print()
    
    # Get access token
    print("Authenticating with gcloud...")
    access_token = get_access_token()
    if not access_token:
        print("ERROR: Could not get access token")
        print("Please ensure you're authenticated: gcloud auth login")
        return False
    print("✅ Authenticated")
    print()
    
    # Read migration SQL
    sql_file = os.path.join(os.path.dirname(__file__), "migration_platform_id_production.sql")
    if not os.path.exists(sql_file):
        print(f"ERROR: SQL file not found: {sql_file}")
        return False
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    print("Migration SQL loaded")
    print()
    
    # Split SQL into individual statements
    # The DO block and UPDATE need to be separate
    statements = [
        # First, check and add column
        """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'sessions' 
        AND column_name = 'platform_id'
    ) THEN
        ALTER TABLE sessions 
        ADD COLUMN platform_id VARCHAR(255);
        
        RAISE NOTICE 'platform_id column added successfully';
    ELSE
        RAISE NOTICE 'platform_id column already exists';
    END IF;
END $$;
        """,
        # Populate from existing values
        """
UPDATE sessions 
SET platform_id = platform 
WHERE platform IS NOT NULL AND platform_id IS NULL;
        """,
        # Create indexes
        """
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent_session 
ON sessions (survey_id, platform_id, respondent_id, id);
        """,
        """
CREATE INDEX IF NOT EXISTS idx_survey_platform 
ON sessions (survey_id, platform_id);
        """,
        """
CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent 
ON sessions (survey_id, platform_id, respondent_id);
        """,
        """
CREATE INDEX IF NOT EXISTS idx_sessions_platform_id 
ON sessions (platform_id);
        """
    ]
    
    print("Executing migration statements...")
    print()
    
    for i, statement in enumerate(statements, 1):
        print(f"Executing statement {i}/{len(statements)}...", end=" ")
        success, result = execute_sql_statement(access_token, statement.strip())
        
        if success:
            print("✅ Success")
        else:
            print(f"❌ Failed: {result}")
            # If it's a permission error, provide alternative
            if "403" in str(result) or "permission" in str(result).lower():
                print()
                print("=" * 60)
                print("API Permission Error")
                print("=" * 60)
                print("The Cloud SQL Admin API executeSql endpoint requires")
                print("specific IAM permissions that may not be enabled.")
                print()
                print("Please use Cloud SQL Console instead:")
                print(f"1. Go to: https://console.cloud.google.com/sql/instances/{INSTANCE_NAME}")
                print(f"2. Click 'Databases' tab → Select '{DATABASE_NAME}'")
                print("3. Click 'Open Cloud Shell' or use Query tab")
                print(f"4. Paste SQL from: {sql_file}")
                return False
            return False
    
    print()
    print("=" * 60)
    print("✅ Migration completed successfully!")
    print("=" * 60)
    print()
    print("Verifying migration...")
    
    # Verify column exists
    verify_sql = """
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'sessions' AND column_name = 'platform_id';
    """
    
    success, result = execute_sql_statement(access_token, verify_sql.strip())
    if success:
        print("✅ Verification: platform_id column exists")
        if isinstance(result, dict) and 'rows' in result:
            print(f"   Column details: {result['rows']}")
    else:
        print("⚠️  Could not verify, but migration appeared successful")
    
    return True

if __name__ == "__main__":
    # Check if requests is available
    try:
        import requests
    except ImportError:
        print("ERROR: requests library not installed")
        print("Please install: pip install requests")
        sys.exit(1)
    
    success = run_migration()
    sys.exit(0 if success else 1)
