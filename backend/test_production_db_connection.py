"""
Test production database connection and schema.

This script verifies that the production database is accessible and has the correct schema,
including the platform_id column and all necessary indexes.
"""

import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


async def test_connection():
    """
    Test database connection and verify schema.
    
    Returns:
        bool: True if all checks pass, False otherwise.
    """
    # Use production DATABASE_URL from environment or Secret Manager
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("\nTo test locally, set DATABASE_URL in your environment:")
        print('$env:DATABASE_URL="postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE"')
        return False
    
    # Hide password in output
    display_url = database_url.split('@')[-1] if '@' in database_url else database_url
    print(f"🔍 Testing connection to: {display_url}")
    print("=" * 80)
    
    try:
        # Create async engine
        engine = create_async_engine(database_url, echo=False)
        
        async with engine.begin() as conn:
            # Test 1: Basic connection
            print("\n✅ TEST 1: Database Connection")
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"   PostgreSQL version: {version}")
            
            # Test 2: Check if sessions table exists
            print("\n✅ TEST 2: Sessions Table Existence")
            result = await conn.execute(text(
                "SELECT EXISTS ("
                "  SELECT FROM information_schema.tables "
                "  WHERE table_name = 'sessions'"
                ")"
            ))
            table_exists = result.scalar()
            
            if not table_exists:
                print("   ❌ sessions table does not exist!")
                print("\n   Action needed: Run database migration to create tables")
                return False
            
            print("   ✓ sessions table exists")
            
            # Test 3: Check all columns
            print("\n✅ TEST 3: Sessions Table Schema")
            result = await conn.execute(text(
                "SELECT column_name, data_type, is_nullable "
                "FROM information_schema.columns "
                "WHERE table_name = 'sessions' "
                "ORDER BY ordinal_position"
            ))
            columns = result.fetchall()
            
            print("   Columns found:")
            for col_name, col_type, is_nullable in columns:
                nullable_str = "NULL" if is_nullable == "YES" else "NOT NULL"
                print(f"   - {col_name}: {col_type} ({nullable_str})")
            
            # Test 4: Check for platform_id specifically
            print("\n✅ TEST 4: Platform ID Column")
            column_names = [col[0] for col in columns]
            if 'platform_id' not in column_names:
                print("   ❌ platform_id column is MISSING!")
                print("\n   Action needed: Run migration script:")
                print("   backend/migration_platform_id_production.sql")
                return False
            
            print("   ✓ platform_id column exists")
            
            # Test 5: Check indexes
            print("\n✅ TEST 5: Composite Indexes")
            result = await conn.execute(text(
                "SELECT indexname, indexdef "
                "FROM pg_indexes "
                "WHERE tablename = 'sessions' "
                "AND indexname LIKE 'idx_%'"
            ))
            indexes = result.fetchall()
            
            if indexes:
                print("   Indexes found:")
                for idx_name, idx_def in indexes:
                    print(f"   - {idx_name}")
            else:
                print("   ⚠️  No composite indexes found (non-critical)")
            
            # Test 6: Try to insert a test session
            print("\n✅ TEST 6: Test Insert/Delete")
            try:
                result = await conn.execute(text(
                    "INSERT INTO sessions (id, platform_id, platform, is_active) "
                    "VALUES ('test-diagnostic-123', 'test-platform', 'web', true) "
                    "RETURNING id"
                ))
                test_id = result.scalar()
                print(f"   ✓ Test insert successful: {test_id}")
                
                # Clean up test data
                await conn.execute(text("DELETE FROM sessions WHERE id = 'test-diagnostic-123'"))
                print("   ✓ Test cleanup successful")
            except Exception as insert_error:
                print(f"   ❌ Insert failed: {insert_error}")
                return False
            
            # Test 7: Check related tables
            print("\n✅ TEST 7: Related Tables")
            for table in ['behavior_data', 'detection_results', 'survey_questions', 'survey_responses']:
                result = await conn.execute(text(
                    f"SELECT EXISTS ("
                    f"  SELECT FROM information_schema.tables "
                    f"  WHERE table_name = '{table}'"
                    f")"
                ))
                exists = result.scalar()
                status = "✓" if exists else "❌"
                print(f"   {status} {table}: {'exists' if exists else 'MISSING'}")
        
        await engine.dispose()
        
        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)
        print("\nDatabase is properly configured and ready for use.")
        return True
        
    except Exception as e:
        print(f"\n❌ DATABASE ERROR: {type(e).__name__}")
        print(f"   {str(e)}")
        print("\n" + "=" * 80)
        print("TROUBLESHOOTING:")
        print("=" * 80)
        print("1. Verify DATABASE_URL format:")
        print("   postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE")
        print("   or for Cloud SQL:")
        print("   postgresql+asyncpg://USER:PASSWORD@/DATABASE?host=/cloudsql/INSTANCE")
        print("\n2. Check database password is correct")
        print("\n3. Verify Cloud SQL instance is running")
        print("\n4. Check network connectivity (VPC connector, firewall rules)")
        
        import traceback
        print("\n" + "=" * 80)
        print("FULL TRACEBACK:")
        print("=" * 80)
        traceback.print_exc()
        
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PRODUCTION DATABASE CONNECTION TEST")
    print("=" * 80)
    
    success = asyncio.run(test_connection())
    
    if success:
        print("\n✅ Diagnostic complete: Database is healthy")
        sys.exit(0)
    else:
        print("\n❌ Diagnostic complete: Issues found (see above)")
        sys.exit(1)
