"""
Script to run the fraud detection migration.

This script executes the SQL migration to create fraud detection tables
and update existing tables with fraud detection columns.
"""

import asyncio
import asyncpg
import os
from pathlib import Path

from app.config import settings


async def run_migration():
    """Run the fraud detection migration."""
    # Parse DATABASE_URL
    db_url = settings.DATABASE_URL
    
    # Convert asyncpg URL format (postgresql+asyncpg://...) to standard postgresql://
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    print("Connecting to database...")
    print(f"Database URL: {db_url.split('@')[0]}@****/{db_url.split('/')[-1]}")
    
    # Read the migration SQL file
    migration_file = Path(__file__).parent / "migrations" / "add_fraud_detection_tables.sql"
    
    if not migration_file.exists():
        print(f"Error: Migration file not found: {migration_file}")
        return False
    
    print(f"Reading migration file: {migration_file}")
    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    # Extract connection details from URL
    # Format: postgresql://user:password@host:port/database
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "")
    
    # Parse connection string
    if "@" in db_url:
        auth_part, rest = db_url.split("@", 1)
        if ":" in auth_part:
            user, password = auth_part.split(":", 1)
        else:
            user = auth_part
            password = ""
    else:
        user = "postgres"
        password = ""
        rest = db_url
    
    if "/" in rest:
        host_port, database = rest.rsplit("/", 1)
        if ":" in host_port:
            host, port = host_port.split(":", 1)
            port = int(port)
        else:
            host = host_port
            port = 5432
    else:
        host = "localhost"
        port = 5432
        database = rest
    
    try:
        print(f"Connecting to {database} on {host}:{port}...")
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        print("Connection established. Running migration...")
        print("-" * 60)
        
        # Split SQL into statements, handling DO blocks and other multi-statement constructs
        import re
        
        # Remove comments (both -- and /* */ style)
        sql_no_comments = re.sub(r'--.*?$', '', migration_sql, flags=re.MULTILINE)
        sql_no_comments = re.sub(r'/\*.*?\*/', '', sql_no_comments, flags=re.DOTALL)
        
        # Split by semicolon, but preserve DO blocks as single statements
        statements = []
        current_stmt = []
        in_do_block = False
        brace_count = 0
        
        lines = sql_no_comments.split('\n')
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_stmt:
                    current_stmt.append('')
                continue
                
            # Detect start of DO block
            if 'DO $$' in stripped or 'DO $' in stripped:
                in_do_block = True
                brace_count = 0
                current_stmt = [line]
                continue
            
            if in_do_block:
                current_stmt.append(line)
                # Count dollar-quoted strings and braces
                if '$$' in stripped:
                    # End of DO block
                    statements.append('\n'.join(current_stmt))
                    current_stmt = []
                    in_do_block = False
                    continue
            else:
                # Regular statement - accumulate until semicolon
                if stripped.endswith(';'):
                    # End of statement
                    current_stmt.append(line)
                    stmt_text = '\n'.join(current_stmt).strip()
                    if stmt_text:
                        statements.append(stmt_text)
                    current_stmt = []
                else:
                    current_stmt.append(line)
        
        # Add any remaining statement
        if current_stmt:
            stmt_text = '\n'.join(current_stmt).strip()
            if stmt_text:
                statements.append(stmt_text)
        
        # Execute each statement
        async with conn.transaction():
            executed = 0
            for i, statement in enumerate(statements, 1):
                statement = statement.strip()
                if not statement or statement == ';':
                    continue
                
                try:
                    # Execute statement
                    await conn.execute(statement)
                    executed += 1
                except Exception as e:
                    error_msg = str(e)
                    # Skip if already exists (idempotent operations)
                    if any(keyword in error_msg.lower() for keyword in ['already exists', 'duplicate', 'if not exists']):
                        print(f"  [SKIP] Statement {i}: {error_msg[:80]}")
                    else:
                        print(f"  [ERROR] Statement {i} failed: {error_msg[:100]}")
                        print(f"  Statement: {statement[:200]}...")
                        raise
        
        print(f"-" * 60)
        print(f"Migration completed! Executed {executed} statements.")
        
        # Verify tables were created
        print("\nVerifying migration...")
        
        # Check fraud_indicators table
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'fraud_indicators'
            )
        """)
        
        if table_exists:
            print("[OK] fraud_indicators table exists")
        else:
            print("[ERROR] fraud_indicators table not found")
        
        # Check device_fingerprint column in sessions
        column_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'sessions' 
                AND column_name = 'device_fingerprint'
            )
        """)
        
        if column_exists:
            print("[OK] device_fingerprint column exists in sessions table")
        else:
            print("[ERROR] device_fingerprint column not found in sessions table")
        
        # Check fraud_score column in detection_results
        fraud_score_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'detection_results' 
                AND column_name = 'fraud_score'
            )
        """)
        
        if fraud_score_exists:
            print("[OK] fraud_score column exists in detection_results table")
        else:
            print("[ERROR] fraud_score column not found in detection_results table")
        
        # Check hierarchical fields in fraud_indicators
        hierarchical_fields = ['survey_id', 'platform_id', 'respondent_id']
        for field in hierarchical_fields:
            field_exists = await conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'fraud_indicators' 
                    AND column_name = '{field}'
                )
            """)
            
            if field_exists:
                print(f"[OK] {field} column exists in fraud_indicators table")
            else:
                print(f"[ERROR] {field} column not found in fraud_indicators table")
        
        # Check hierarchical indexes
        indexes_to_check = [
            'idx_fraud_survey',
            'idx_fraud_survey_platform',
            'idx_fraud_survey_platform_respondent',
            'idx_fraud_survey_platform_respondent_session'
        ]
        
        print("\nChecking hierarchical indexes...")
        for index_name in indexes_to_check:
            index_exists = await conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT FROM pg_indexes 
                    WHERE indexname = '{index_name}'
                )
            """)
            
            if index_exists:
                print(f"[OK] {index_name} index exists")
            else:
                print(f"[WARNING] {index_name} index not found (may already exist or failed to create)")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"\nError running migration: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Fraud Detection Migration")
    print("=" * 60)
    print()
    
    success = asyncio.run(run_migration())
    
    if success:
        print("\n[SUCCESS] Migration completed successfully!")
        exit(0)
    else:
        print("\n[FAILED] Migration failed. Please check the errors above.")
        exit(1)
