"""
Run platform_id migration on production Cloud SQL using gcloud CLI.

This script uses gcloud sql databases execute-sql to run the migration
directly on the production database without requiring psql.
"""

import os
import sys
import subprocess
import tempfile
import json

# GCP Configuration
PROJECT_ID = "survey-bot-detection"
INSTANCE_NAME = "bot-db"
DATABASE_NAME = "bot_detection"
REGION = "northamerica-northeast2"

def run_gcloud_command(cmd, description):
    """Run a gcloud command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"Error running command: {e}", file=sys.stderr)
        return False, "", str(e)

def check_column_exists():
    """Check if platform_id column exists."""
    check_sql = """
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'sessions' AND column_name = 'platform_id';
    """
    
    # Save SQL to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        f.write(check_sql)
        temp_file = f.name
    
    try:
        cmd = [
            "gcloud", "sql", "databases", "execute-sql", DATABASE_NAME,
            "--instance", INSTANCE_NAME,
            "--file", temp_file,
            "--project", PROJECT_ID,
            "--quiet"
        ]
        
        success, stdout, stderr = run_gcloud_command(cmd, "Checking if platform_id column exists")
        
        if success:
            # Check if column exists in output
            if "platform_id" in stdout.lower():
                print("✅ platform_id column already exists")
                return True
            else:
                print("❌ platform_id column does not exist")
                return False
        else:
            print("⚠️  Could not check column status. Proceeding with migration...")
            return False
            
    except Exception as e:
        print(f"Error checking column: {e}")
        return False
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def run_migration():
    """Run the platform_id migration."""
    print("\n" + "="*60)
    print("Platform ID Migration for Production Cloud SQL")
    print("="*60)
    print(f"Project: {PROJECT_ID}")
    print(f"Instance: {INSTANCE_NAME}")
    print(f"Database: {DATABASE_NAME}")
    print("="*60 + "\n")
    
    # Migration SQL - using DO block for safety
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
        -- Add platform_id column
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
    
    # Save SQL to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False, encoding='utf-8') as f:
        f.write(migration_sql)
        temp_file = f.name
    
    print(f"Migration SQL saved to: {temp_file}\n")
    
    try:
        # Execute migration using gcloud
        cmd = [
            "gcloud", "sql", "databases", "execute-sql", DATABASE_NAME,
            "--instance", INSTANCE_NAME,
            "--file", temp_file,
            "--project", PROJECT_ID,
            "--quiet"
        ]
        
        success, stdout, stderr = run_gcloud_command(cmd, "Executing migration SQL")
        
        if success:
            print("\n" + "="*60)
            print("✅ Migration completed successfully!")
            print("="*60)
            
            # Verify the migration
            print("\nVerifying migration...")
            if check_column_exists():
                print("\n✅ Verification: platform_id column exists")
            else:
                print("\n⚠️  Verification: Could not confirm column exists, but migration appeared successful")
            
            return True
        else:
            print("\n" + "="*60)
            print("❌ Migration failed!")
            print("="*60)
            print("\nError output:")
            print(stderr)
            print("\nYou may need to run the SQL manually in Cloud SQL Console:")
            print(f"1. Go to: https://console.cloud.google.com/sql/instances/{INSTANCE_NAME}")
            print("2. Click on 'Databases' tab")
            print(f"3. Select database: {DATABASE_NAME}")
            print("4. Click 'Open Cloud Shell' or use Query tab")
            print("5. Paste and run the SQL from the file above")
            return False
            
    except Exception as e:
        print(f"\n❌ Error executing migration: {e}")
        print("\nAlternative: Run SQL manually in Cloud SQL Console")
        print(f"SQL file location: {temp_file}")
        return False
    finally:
        # Don't delete temp file immediately - user might need it
        print(f"\nNote: SQL file saved at: {temp_file}")
        print("You can delete it manually after verifying the migration.")

if __name__ == "__main__":
    # Check if gcloud is installed
    try:
        result = subprocess.run(
            ["gcloud", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("❌ gcloud CLI is not installed or not in PATH")
            sys.exit(1)
    except FileNotFoundError:
        print("❌ gcloud CLI is not installed or not in PATH")
        print("Please install gcloud CLI: https://cloud.google.com/sdk/docs/install")
        sys.exit(1)
    
    # Check authentication
    try:
        result = subprocess.run(
            ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"],
            capture_output=True,
            text=True
        )
        if not result.stdout.strip():
            print("❌ No active gcloud authentication found")
            print("Please run: gcloud auth login")
            sys.exit(1)
        else:
            print(f"✅ Authenticated as: {result.stdout.strip()}")
    except Exception as e:
        print(f"⚠️  Could not verify authentication: {e}")
        print("Continuing anyway...")
    
    # Run migration
    success = run_migration()
    sys.exit(0 if success else 1)
