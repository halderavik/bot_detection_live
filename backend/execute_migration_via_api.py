"""
Execute SQL migration on Cloud SQL using Cloud SQL Admin API REST endpoint.

This script uses the Cloud SQL Admin API to execute SQL directly on the
production database using the REST API with gcloud authentication.
"""

import os
import sys
import json
import subprocess
import tempfile

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

def execute_sql_via_api(sql_statement):
    """Execute SQL statement via Cloud SQL Admin API REST endpoint."""
    access_token = get_access_token()
    if not access_token:
        return False, "Could not get access token"
    
    import requests
    
    # Cloud SQL Admin API endpoint for executing SQL
    # Note: This endpoint may require specific IAM permissions
    api_url = f"https://sqladmin.googleapis.com/v1/projects/{PROJECT_ID}/instances/{INSTANCE_NAME}/databases/{DATABASE_NAME}/executeSql"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # The API expects a request body with the SQL statement
    payload = {
        "sql": sql_statement
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return True, response.text
        else:
            return False, f"API returned status {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def run_migration():
    """Run the platform_id migration."""
    print("=" * 60)
    print("Platform ID Migration via Cloud SQL Admin API")
    print("=" * 60)
    print(f"Project: {PROJECT_ID}")
    print(f"Instance: {INSTANCE_NAME}")
    print(f"Database: {DATABASE_NAME}")
    print("=" * 60)
    print()
    
    # Read migration SQL from file
    sql_file = os.path.join(os.path.dirname(__file__), "migration_platform_id_production.sql")
    if not os.path.exists(sql_file):
        print(f"ERROR: SQL file not found: {sql_file}")
        return False
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    print("Migration SQL loaded from file")
    print()
    
    # Note: The Cloud SQL Admin API executeSql endpoint may not be available
    # or may require special permissions. Let's try it, but also provide
    # alternative instructions.
    
    print("Attempting to execute SQL via Cloud SQL Admin API...")
    print("(This may require specific IAM permissions)")
    print()
    
    # Try to execute (this may fail if the endpoint isn't available)
    success, message = execute_sql_via_api(migration_sql)
    
    if success:
        print("SUCCESS: Migration executed via API")
        print(message)
        return True
    else:
        print(f"API execution failed: {message}")
        print()
        print("=" * 60)
        print("Manual Execution Required")
        print("=" * 60)
        print()
        print("The Cloud SQL Admin API executeSql endpoint may not be available")
        print("or may require additional IAM permissions.")
        print()
        print("Please use one of these methods:")
        print()
        print("OPTION 1: Cloud SQL Console (Recommended)")
        print(f"  1. Go to: https://console.cloud.google.com/sql/instances/{INSTANCE_NAME}")
        print(f"  2. Click on 'Databases' tab")
        print(f"  3. Select database: {DATABASE_NAME}")
        print("  4. Click 'Open Cloud Shell' or use Query tab")
        print(f"  5. Copy and paste the SQL from: {sql_file}")
        print()
        print("OPTION 2: Cloud Shell")
        print("  1. Open: https://shell.cloud.google.com/")
        print(f"  2. Upload the SQL file: {sql_file}")
        print(f"  3. Run: gcloud sql connect {INSTANCE_NAME} --user=bot_user --database={DATABASE_NAME} --project={PROJECT_ID}")
        print("  4. In psql, run: \\i <path-to-uploaded-file>")
        print()
        print(f"SQL file location: {sql_file}")
        return False

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
