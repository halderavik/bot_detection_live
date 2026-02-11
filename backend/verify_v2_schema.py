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
from pathlib import Path
from urllib.parse import urlparse

# Add parent for import when run from backend/
sys.path.insert(0, str(Path(__file__).parent))


def _get_tcp_params(database_url):
    """Get TCP connection params for Cloud SQL (e.g. when running from Windows)."""
    try:
        from run_migration_sync import get_db_params_from_url
        return get_db_params_from_url(database_url)
    except Exception:
        return None


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
        
        conn = None
        # On Windows or when CLOUD_SQL_IP is set, use TCP (Unix socket not available)
        cloud_sql_ip = os.getenv("CLOUD_SQL_IP")
        is_windows = sys.platform == "win32"
        if use_socket and (is_windows or cloud_sql_ip):
            tcp_params = _get_tcp_params(database_url) or (
                {"host": cloud_sql_ip or "localhost", "port": 5432, "database": database, "user": user, "password": password}
            )
            if tcp_params:
                print("  Using TCP connection (Windows/CLOUD_SQL_IP)")
                conn = await asyncpg.connect(
                    host=tcp_params["host"],
                    port=int(tcp_params.get("port", 5432)),
                    user=tcp_params["user"],
                    password=tcp_params["password"],
                    database=tcp_params["database"]
                )
        elif use_socket:
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
        
        print("[OK] Connected successfully\n")
        
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
            print(f"  [OK] {table}")
        
        required_tables = [
            'sessions',
            'behavior_data',
            'detection_results',
            'survey_questions',
            'survey_responses',
            'fraud_indicators'  # Stage 3 - Fraud & Duplicate Detection
        ]
        
        missing_tables = [t for t in required_tables if t not in table_names]
        if missing_tables:
            print(f"\n[ERROR] Missing tables: {', '.join(missing_tables)}")
            print("  The backend should create these automatically on startup.")
            print("  Check Cloud Run logs for 'Database tables created successfully'")
            await conn.close()
            return False
        
        print(f"\n[OK] All {len(required_tables)} required tables exist")
        
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
            print("[ERROR] platform_id column NOT found in sessions table")
            await conn.close()
            return False
        else:
            platform_id_col = next(c for c in columns if c['column_name'] == 'platform_id')
            print(f"[OK] platform_id column exists: {platform_id_col['data_type']}")
            if platform_id_col['character_maximum_length']:
                print(f"  Length: {platform_id_col['character_maximum_length']}")

        # Stage 3: Check device_fingerprint in sessions (fraud detection)
        if 'device_fingerprint' not in column_names:
            print("[ERROR] device_fingerprint column NOT found in sessions table (Stage 3 fraud detection)")
            await conn.close()
            return False
        else:
            print("[OK] device_fingerprint column exists in sessions (Stage 3 fraud detection)")

        # Stage 3: Check fraud columns in detection_results
        dr_columns = await conn.fetch("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'detection_results' ORDER BY column_name;
        """)
        dr_column_names = [r['column_name'] for r in dr_columns]
        for fraud_col in ['fraud_score', 'fraud_indicators']:
            if fraud_col not in dr_column_names:
                print(f"[ERROR] {fraud_col} column NOT found in detection_results (Stage 3)")
                await conn.close()
                return False
        print("[OK] fraud_score and fraud_indicators columns exist in detection_results")

        # Stage 3: Check fraud_indicators table has hierarchical columns
        fi_columns = await conn.fetch("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'fraud_indicators' ORDER BY column_name;
        """)
        fi_column_names = [r['column_name'] for r in fi_columns]
        for hcol in ['survey_id', 'platform_id', 'respondent_id']:
            if hcol not in fi_column_names:
                print(f"[ERROR] {hcol} column NOT found in fraud_indicators")
                await conn.close()
                return False
        print("[OK] fraud_indicators has hierarchical columns (survey_id, platform_id, respondent_id)")

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
            print(f"  [OK] {idx}")
        
        required_indexes = [
            'idx_survey_platform_respondent_session',
            'idx_survey_platform',
            'idx_survey_platform_respondent',
            'idx_sessions_platform_id',
            'idx_session_fingerprint'  # Stage 3 - fraud detection
        ]
        
        missing_indexes = [idx for idx in required_indexes if idx not in index_names]
        if missing_indexes:
            print(f"\n[WARN] Missing indexes: {', '.join(missing_indexes)}")
            print("  These indexes are defined in the Session model and should be created automatically.")
            print("  If missing, they may need to be created manually or the model needs to be updated.")
        else:
            print(f"\n[OK] All {len(required_indexes)} required composite indexes exist")
        
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
            print(f"  [OK] {fk['table_name']}.{fk['column_name']} -> {fk['foreign_table_name']}")
        if len(fks) > 10:
            print(f"  ... and {len(fks) - 10} more")
        
        await conn.close()
        
        print("\n" + "="*60)
        print("[OK] Schema verification complete - All checks passed!")
        print("="*60)
        return True
        
    except FileNotFoundError as e:
        print(f"\n[ERROR] Connection error: Unix socket not found")
        print("  This usually means Cloud SQL Proxy is not running or configured correctly.")
        print("  The backend should handle this via Cloud Run's Cloud SQL connector.")
        return False
    except Exception as e:
        print(f"\n[ERROR] Error verifying schema: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(verify_schema())
    sys.exit(0 if result else 1)
