"""
Execute platform_id migration by connecting directly to Cloud SQL.

This script extracts connection details from DATABASE_URL and connects
using the public IP of the Cloud SQL instance.
"""

import os
import sys
import subprocess
import re
import psycopg2
from urllib.parse import urlparse, parse_qs

# GCP Configuration
PROJECT_ID = "survey-bot-detection"
INSTANCE_NAME = "bot-db"
DATABASE_NAME = "bot_detection"

def get_database_url():
    """Get DATABASE_URL from Secret Manager."""
    try:
        result = subprocess.run(
            ["gcloud", "secrets", "versions", "access", "latest", 
             "--secret=DATABASE_URL", f"--project={PROJECT_ID}"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"ERROR: Failed to get DATABASE_URL: {e}")
        return None

def get_cloud_sql_public_ip():
    """Get the public IP of the Cloud SQL instance."""
    try:
        result = subprocess.run(
            ["gcloud", "sql", "instances", "describe", INSTANCE_NAME,
             f"--project={PROJECT_ID}", "--format=value(ipAddresses[0].ipAddress)"],
            capture_output=True,
            text=True,
            check=True
        )
        ip = result.stdout.strip()
        if ip:
            return ip
    except Exception as e:
        print(f"WARNING: Could not get public IP: {e}")
    
    # Try alternative method
    try:
        result = subprocess.run(
            ["gcloud", "sql", "instances", "describe", INSTANCE_NAME,
             f"--project={PROJECT_ID}", "--format=json"],
            capture_output=True,
            text=True,
            check=True
        )
        import json
        instance_info = json.loads(result.stdout)
        if 'ipAddresses' in instance_info and len(instance_info['ipAddresses']) > 0:
            return instance_info['ipAddresses'][0].get('ipAddress')
    except Exception as e:
        print(f"WARNING: Could not get public IP: {e}")
    
    return None

def parse_database_url(database_url):
    """Parse DATABASE_URL and extract connection parameters."""
    # Remove asyncpg driver if present
    url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    # Parse the URL
    parsed = urlparse(url)
    
    # Extract credentials
    if parsed.username:
        user = parsed.username
    else:
        # Extract from netloc
        if '@' in parsed.netloc:
            auth = parsed.netloc.split('@')[0]
            if ':' in auth:
                user, password = auth.split(':', 1)
            else:
                user = auth
                password = None
        else:
            user = None
    
    password = parsed.password
    
    # Extract database name
    database = parsed.path.lstrip('/') if parsed.path else DATABASE_NAME
    
    return {
        'user': user,
        'password': password,
        'database': database
    }

def run_migration():
    """Run the platform_id migration."""
    print("=" * 60)
    print("Platform ID Migration - Direct Connection")
    print("=" * 60)
    print(f"Project: {PROJECT_ID}")
    print(f"Instance: {INSTANCE_NAME}")
    print(f"Database: {DATABASE_NAME}")
    print("=" * 60)
    print()
    
    # Get DATABASE_URL
    print("Getting DATABASE_URL from Secret Manager...")
    database_url = get_database_url()
    if not database_url:
        print("ERROR: Could not get DATABASE_URL")
        return False
    print("✅ DATABASE_URL retrieved")
    print()
    
    # Parse connection details
    print("Parsing connection details...")
    conn_params = parse_database_url(database_url)
    print(f"User: {conn_params['user']}")
    print(f"Database: {conn_params['database']}")
    print()
    
    # Get public IP
    print("Getting Cloud SQL public IP...")
    public_ip = get_cloud_sql_public_ip()
    if not public_ip:
        print("ERROR: Could not get Cloud SQL public IP")
        print("The instance may not have a public IP, or it may require authorized networks")
        return False
    print(f"✅ Public IP: {public_ip}")
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
    
    # Connect to database
    print("Connecting to Cloud SQL...")
    try:
        conn = psycopg2.connect(
            host=public_ip,
            port=5432,
            database=conn_params['database'],
            user=conn_params['user'],
            password=conn_params['password'],
            connect_timeout=10
        )
        print("✅ Connected to database")
        print()
        
        # Execute migration
        print("Executing migration...")
        cursor = conn.cursor()
        cursor.execute(migration_sql)
        conn.commit()
        print("✅ Migration executed successfully")
        print()
        
        # Verify
        print("Verifying migration...")
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'sessions' AND column_name = 'platform_id'
        """)
        result = cursor.fetchone()
        
        if result:
            print(f"✅ Verification: platform_id column exists")
            print(f"   Type: {result[1]}({result[2]})")
        else:
            print("⚠️  Warning: Could not verify column exists")
        
        cursor.close()
        conn.close()
        
        print()
        print("=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        return True
        
    except psycopg2.OperationalError as e:
        if "timeout" in str(e).lower() or "connection" in str(e).lower():
            print("ERROR: Could not connect to Cloud SQL")
            print("The instance may require authorized networks or Cloud SQL Proxy")
            print()
            print("Please use Cloud SQL Console instead:")
            print(f"1. Go to: https://console.cloud.google.com/sql/instances/{INSTANCE_NAME}")
            print(f"2. Click 'Databases' tab -> Select '{DATABASE_NAME}'")
            print("3. Click 'Open Cloud Shell' or use Query tab")
            print(f"4. Paste SQL from: {sql_file}")
        else:
            print(f"ERROR: Database error: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Check if psycopg2 is available
    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 library not installed")
        print("Please install: pip install psycopg2-binary")
        sys.exit(1)
    
    success = run_migration()
    sys.exit(0 if success else 1)
