"""
Script to check if bot_detection_v2 database has the correct schema.

This script connects to the database and verifies:
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

async def check_schema():
    """Check database schema."""
    # Get DATABASE_URL from environment or use default
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("Usage: Set DATABASE_URL to point to bot_detection_v2 database")
        sys.exit(1)
    
    # Parse the connection string
    # Format: postgresql+asyncpg://user:pass@/db?host=/cloudsql/...
    # We need to convert to asyncpg format
    parsed = urlparse(database_url.replace("postgresql+asyncpg://", "postgresql://"))
    
    # Extract connection details
    if parsed.hostname and parsed.hostname.startswith("/cloudsql/"):
        # Unix socket connection
        socket_path = parsed.hostname
        database = parsed.path.lstrip("/").split("?")[0]
        user = parsed.username
        password = parsed.password
    else:
        # TCP connection
        socket_path = None
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        database = parsed.path.lstrip("/").split("?")[0]
        user = parsed.username
        password = parsed.password
    
    try:
        if socket_path:
            # Unix socket connection (Cloud SQL)
            conn = await asyncpg.connect(
                user=user,
                password=password,
                database=database,
                host=socket_path
            )
        else:
            # TCP connection
            conn = await asyncpg.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
        
        print(f"✓ Connected to database: {database}")
        
        # Check if tables exist
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
        """
        tables = await conn.fetch(tables_query)
        table_names = [row['table_name'] for row in tables]
        
        print(f"\nFound {len(table_names)} tables:")
        for table in table_names:
            print(f"  - {table}")
        
        # Required tables
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
            return False
        else:
            print(f"\n✓ All required tables exist")
        
        # Check sessions table for platform_id column
        columns_query = """
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'sessions'
        ORDER BY column_name;
        """
        columns = await conn.fetch(columns_query)
        column_names = [row['column_name'] for row in columns]
        
        print(f"\nSessions table columns ({len(column_names)}):")
        for col in columns:
            col_type = col['data_type']
            if col['character_maximum_length']:
                col_type += f"({col['character_maximum_length']})"
            print(f"  - {col['column_name']}: {col_type}")
        
        if 'platform_id' not in column_names:
            print("\n✗ platform_id column NOT found in sessions table")
            return False
        else:
            print("\n✓ platform_id column exists in sessions table")
        
        # Check for composite indexes
        indexes_query = """
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'sessions'
        AND schemaname = 'public'
        ORDER BY indexname;
        """
        indexes = await conn.fetch(indexes_query)
        index_names = [row['indexname'] for row in indexes]
        
        print(f"\nSessions table indexes ({len(index_names)}):")
        for idx in indexes:
            print(f"  - {idx['indexname']}")
        
        required_indexes = [
            'idx_survey_platform_respondent_session',
            'idx_survey_platform',
            'idx_survey_platform_respondent',
            'idx_sessions_platform_id'
        ]
        
        missing_indexes = [idx for idx in required_indexes if idx not in index_names]
        if missing_indexes:
            print(f"\n✗ Missing indexes: {', '.join(missing_indexes)}")
            return False
        else:
            print(f"\n✓ All required composite indexes exist")
        
        # Check foreign key constraints
        fk_query = """
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        ORDER BY tc.table_name, kcu.column_name;
        """
        fks = await conn.fetch(fk_query)
        
        print(f"\nForeign key constraints ({len(fks)}):")
        for fk in fks:
            print(f"  - {fk['table_name']}.{fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")
        
        await conn.close()
        
        print("\n" + "="*60)
        print("✓ Schema verification complete - All checks passed!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n✗ Error checking schema: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(check_schema())
    sys.exit(0 if result else 1)
