"""
Synchronous fraud detection migration for production database.

Uses psycopg2 (like run_migration_sync.py) to avoid async/Unix socket
issues on Windows. Handles Cloud SQL connection via public IP.

Run before deploying Stage 3 (Fraud & Duplicate Detection) updates.
Requires: DATABASE_URL (and optionally CLOUD_SQL_IP for Cloud SQL).
"""

import os
import re
import sys
from pathlib import Path

# Import connection helper from existing migration script
sys.path.insert(0, str(Path(__file__).parent))
from run_migration_sync import get_db_params_from_url


def split_sql_statements(sql_content: str):
    """
    Split SQL into executable statements while preserving DO $$ ... $$ blocks.

    Returns:
        List of SQL statement strings.
    """
    # Remove line comments (-- ...)
    sql_no_comments = re.sub(r"--[^\n]*", "\n", sql_content)
    # Remove block comments (/* ... */)
    sql_no_comments = re.sub(r"/\*.*?\*/", "", sql_no_comments, flags=re.DOTALL)

    statements = []
    current = []
    in_do_block = False

    for line in sql_no_comments.split("\n"):
        stripped = line.strip()
        if not stripped and not current:
            continue

        # Start of DO block
        if "DO $$" in stripped or "DO $" in stripped:
            in_do_block = True
            current = [line]
            continue

        if in_do_block:
            current.append(line)
            if "$$" in stripped and "DO" not in stripped:
                stmt = "\n".join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
                in_do_block = False
            continue

        # Regular statement
        current.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(current).strip()
            if stmt and stmt != ";":
                statements.append(stmt)
            current = []

    if current:
        stmt = "\n".join(current).strip()
        if stmt:
            statements.append(stmt)

    return statements


def run_fraud_migration():
    """Run the fraud detection tables migration."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("\nTo use this script:")
        print("  $env:DATABASE_URL = 'postgresql+asyncpg://bot_user:PASSWORD@/bot_detection_v2?host=/cloudsql/...'")
        print("  python run_fraud_migration_sync.py")
        sys.exit(1)

    migration_file = Path(__file__).parent / "migrations" / "add_fraud_detection_tables.sql"
    if not migration_file.exists():
        print(f"ERROR: Migration file not found: {migration_file}")
        sys.exit(1)

    with open(migration_file, "r", encoding="utf-8") as f:
        migration_sql = f.read()

    params = get_db_params_from_url(database_url)
    print(f"Connecting to database: {params['database']} on {params['host']}:{params['port']}")

    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)

    try:
        conn = psycopg2.connect(**params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        print("Connected. Running fraud detection migration...")

        statements = split_sql_statements(migration_sql)
        executed = 0
        for i, stmt in enumerate(statements):
            stmt = stmt.strip()
            if not stmt:
                continue
            try:
                cursor.execute(stmt)
                executed += 1
                # Brief label for first few key operations
                if "fraud_indicators" in stmt[:100] and "CREATE" in stmt:
                    print("  Created fraud_indicators table")
                elif "device_fingerprint" in stmt:
                    print("  Added device_fingerprint to sessions")
                elif "fraud_score" in stmt:
                    print("  Added fraud columns to detection_results")
            except Exception as e:
                msg = str(e).lower()
                if any(k in msg for k in ["already exists", "duplicate", "if not exists"]):
                    print(f"  [SKIP] {e.args[0][:60]}...")
                else:
                    print(f"ERROR executing statement {i + 1}: {e}")
                    cursor.close()
                    conn.close()
                    sys.exit(1)

        cursor.close()
        conn.close()

        print(f"\nMigration completed. Executed {executed} statements.")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 60)
    print("Fraud Detection Migration (Stage 3)")
    print("=" * 60)
    print()
    run_fraud_migration()
    print("\nDone. Run verify_v2_schema.py to confirm schema is ready.")
