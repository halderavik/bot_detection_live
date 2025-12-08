"""
Synchronous migration runner for production database.
Uses psycopg2 instead of asyncpg to avoid Unix socket issues on Windows.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import urlparse

def get_db_params_from_url(database_url):
    """Parse DATABASE_URL and return connection parameters for TCP connection."""
    # Remove asyncpg driver if present
    url = database_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    # Handle Unix socket format (common in Cloud SQL)
    # Format: postgresql://user:password@/database?host=/cloudsql/project:region:instance
    if '/cloudsql/' in url or url.count('@') == 1 and not url.split('@')[1].startswith('/') and '/' in url.split('@')[1]:
        # Extract user, password, database from Unix socket format
        import re
        from urllib.parse import parse_qs, urlparse as uparse
        
        # Pattern: postgresql://user:password@/database?host=...
        match = re.match(r'postgresql://([^:]+):([^@]+)@/([^?]+)', url)
        if match:
            user, password, database = match.groups()
            # Use public IP for TCP connection (Cloud SQL instance IP)
            # This will be overridden by command line or environment variable if provided
            cloud_sql_ip = os.getenv('CLOUD_SQL_IP', '34.130.80.8')
            return {
                'host': cloud_sql_ip,
                'port': 5432,
                'database': database,
                'user': user,
                'password': password
            }
    
    # Standard URL parsing for TCP connections
    try:
        parsed = urlparse(url)
        port = parsed.port
        if port is None:
            port = 5432
        else:
            port = int(port)
    except (ValueError, AttributeError):
        port = 5432
    
    # Extract host, user, password
    netloc = parsed.netloc
    if '@' in netloc:
        auth, hostport = netloc.rsplit('@', 1)
        if ':' in auth:
            user, password = auth.split(':', 1)
        else:
            user = auth
            password = None
        if ':' in hostport:
            host = hostport.rsplit(':', 1)[0]
        else:
            host = hostport
    else:
        user = parsed.username
        password = parsed.password
        if ':' in netloc:
            host = netloc.rsplit(':', 1)[0]
        else:
            host = netloc
    
    return {
        'host': host or 'localhost',
        'port': port,
        'database': parsed.path[1:] if parsed.path and parsed.path != '/' else 'bot_detection',
        'user': user,
        'password': password
    }

def run_migration():
    """Run the migration to add platform_id and indexes."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        # Parse connection parameters
        params = get_db_params_from_url(database_url)
        print(f"Connecting to database: {params['database']} on {params['host']}:{params['port']}")
        
        # Connect to database
        conn = psycopg2.connect(**params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Connected to database")
        
        # Check if platform_id column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='sessions' AND column_name='platform_id'
        """)
        column_exists = cursor.fetchone() is not None
        
        if not column_exists:
            print("Adding platform_id column to sessions table...")
            # Add platform_id column
            cursor.execute("""
                ALTER TABLE sessions 
                ADD COLUMN platform_id VARCHAR(50)
            """)
            print("✅ platform_id column added successfully")
            
            # Populate platform_id from existing platform values
            print("Populating platform_id from existing platform values...")
            cursor.execute("""
                UPDATE sessions 
                SET platform_id = platform 
                WHERE platform IS NOT NULL AND platform_id IS NULL
            """)
            rows_updated = cursor.rowcount
            print(f"✅ platform_id populated from {rows_updated} existing platform values")
        else:
            print("ℹ️  platform_id column already exists, skipping creation")
        
        # Create indexes
        print("Creating composite indexes...")
        
        indexes = [
            ("idx_survey_platform_respondent_session", 
             "CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent_session ON sessions (survey_id, platform_id, respondent_id, id)"),
            ("idx_survey_platform", 
             "CREATE INDEX IF NOT EXISTS idx_survey_platform ON sessions (survey_id, platform_id)"),
            ("idx_survey_platform_respondent", 
             "CREATE INDEX IF NOT EXISTS idx_survey_platform_respondent ON sessions (survey_id, platform_id, respondent_id)"),
            ("idx_sessions_platform_id", 
             "CREATE INDEX IF NOT EXISTS idx_sessions_platform_id ON sessions (platform_id)"),
            ("idx_sessions_survey_id", 
             "CREATE INDEX IF NOT EXISTS idx_sessions_survey_id ON sessions (survey_id)"),
            ("idx_sessions_respondent_id", 
             "CREATE INDEX IF NOT EXISTS idx_sessions_respondent_id ON sessions (respondent_id)")
        ]
        
        for index_name, index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"✅ Created index: {index_name}")
            except Exception as e:
                print(f"⚠️  Index {index_name} may already exist: {e}")
        
        print("\n✅ Migration completed successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_migration()

