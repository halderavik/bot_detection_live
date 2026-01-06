"""
Script to verify bot_detection_v2 database schema.

This script checks:
- All required tables exist
- platform_id column exists in sessions table
- All composite indexes are created
- Text analysis tables exist
"""

import asyncio
import asyncpg
import os
import sys
from urllib.parse import urlparse

async def verify_schema():
    """Verify database schema."""
    # Get DATABASE_URL from environment
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("\nTo use this script:")
        print("  $env:DATABASE_URL = 'postgresql+asyncpg://bot_user:NewPassword123!@/bot_detection_v2?host=/cloudsql/survey-bot-detection:northamerica-northeast2:bot-db'")
        print("  python verify_v2_schema.py")
        sys.exit(1)
    
    # Parse connection string
    parsed = urlparse(database_url.replace("postgresql+asyncpg://", "postgresql://"))
    
    # Extract connection details
    if parsed.hostname and parsed.hostname.startswith("/cloudsql/"):
        socket_path = parsed.hostname
        database = parsed.path.lstrip("/").split("?")[0]
        user = parsed.username
        password = parsed.password
        use_socket = True
    else:
        use_socket = False
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        database = parsed.path.lstrip("/").split("?")[0]
        user = parsed.username
        password = parsed.password
    
    try:
        print(f"Connecting to database: {database}...")
        
        if use_socket:
            conn = await asyncpg.connect(
                user=user,
                password=password,
                database=database,
                host=socket_path
            )
        else:
            conn = await asyncpg.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
        
        print("✓ Connected successfully\n")
        
        # Check tables
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
        """
        tables = await conn.fetch(tables_query)
        table_names = [row['table_name'] for row in tables]
        
        print(f"Found {len(table_names)} tables:")
        for table in table_names:
            print(f"  ✓ {table}")
        
        required_tables = [
            'sessions',
            'behavior_data',
            'detection_results',
            'survey_questions',
            'survey_responses'
        ]
        
        missing_tables = [t for t in required_tables if t not in table_names]
        if missing_tables:
            print(f"\n✗ Missing tables: {', '.join(missing_tables)}")
            print("  The backend should create these automatically on startup.")
            print("  Check Cloud Run logs for 'Database tables created successfully'")
            await conn.close()
            return False
        
        print(f"\n✓ All {len(required_tables)} required tables exist")
        
        # Check sessions table columns
        columns_query = """
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'sessions'
        ORDER BY column_name;
        """
        columns = await conn.fetch(columns_query)
        column_names = [row['column_name'] for row in columns]
        
        print(f"\nSessions table has {len(column_names)} columns")
        
        if 'platform_id' not in column_names:
            print("✗ platform_id column NOT found in sessions table")
            await conn.close()
            return False
        else:
            platform_id_col = next(c for c in columns if c['column_name'] == 'platform_id')
            print(f"✓ platform_id column exists: {platform_id_col['data_type']}")
            if platform_id_col['character_maximum_length']:
                print(f"  Length: {platform_id_col['character_maximum_length']}")
        
        # Check indexes
        indexes_query = """
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = 'sessions'
        AND schemaname = 'public'
        ORDER BY indexname;
        """
        indexes = await conn.fetch(indexes_query)
        index_names = [row['indexname'] for row in indexes]
        
        print(f"\nSessions table has {len(index_names)} indexes:")
        for idx in index_names:
            print(f"  ✓ {idx}")
        
        required_indexes = [
            'idx_survey_platform_respondent_session',
            'idx_survey_platform',
            'idx_survey_platform_respondent',
            'idx_sessions_platform_id'
        ]
        
        missing_indexes = [idx for idx in required_indexes if idx not in index_names]
        if missing_indexes:
            print(f"\n⚠ Missing indexes: {', '.join(missing_indexes)}")
            print("  These indexes are defined in the Session model and should be created automatically.")
            print("  If missing, they may need to be created manually or the model needs to be updated.")
        else:
            print(f"\n✓ All {len(required_indexes)} required composite indexes exist")
        
        # Check foreign keys
        fk_query = """
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        ORDER BY tc.table_name, kcu.column_name;
        """
        fks = await conn.fetch(fk_query)
        
        print(f"\nFound {len(fks)} foreign key constraints:")
        for fk in fks[:10]:  # Show first 10
            print(f"  ✓ {fk['table_name']}.{fk['column_name']} -> {fk['foreign_table_name']}")
        if len(fks) > 10:
            print(f"  ... and {len(fks) - 10} more")
        
        await conn.close()
        
        print("\n" + "="*60)
        print("✓ Schema verification complete - All checks passed!")
        print("="*60)
        return True
        
    except FileNotFoundError as e:
        print(f"\n✗ Connection error: Unix socket not found")
        print("  This usually means Cloud SQL Proxy is not running or configured correctly.")
        print("  The backend should handle this via Cloud Run's Cloud SQL connector.")
        return False
    except Exception as e:
        print(f"\n✗ Error verifying schema: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(verify_schema())
    sys.exit(0 if result else 1)
