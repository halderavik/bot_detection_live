"""
Simple database connection test.
"""

import asyncio
import sys
from app.database import engine, AsyncSessionLocal
from app.config import settings

async def test_connection():
    """Test database connection."""
    print("=" * 60)
    print("Testing Database Connection")
    print("=" * 60)
    print(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'N/A'}")
    print()
    
    try:
        # Test 1: Basic connection
        print("Test 1: Testing basic connection...")
        async with engine.connect() as conn:
            result = await conn.execute("SELECT 1")
            row = result.fetchone()
            if row and row[0] == 1:
                print("[PASS] Basic connection successful")
            else:
                print("[FAIL] Connection returned unexpected result")
                return False
        print()
        
        # Test 2: Create a session
        print("Test 2: Testing session creation...")
        from app.models import Session
        async with AsyncSessionLocal() as db:
            test_session = Session(
                user_agent="Connection Test",
                platform="test",
                platform_id="test"
            )
            db.add(test_session)
            await db.commit()
            session_id = test_session.id
            print(f"[PASS] Session created successfully: {session_id}")
            
            # Clean up
            await db.delete(test_session)
            await db.commit()
            print("[PASS] Test session cleaned up")
        print()
        
        # Test 3: Check if tables exist
        print("Test 3: Checking database tables...")
        async with engine.connect() as conn:
            result = await conn.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in result.fetchall()]
            print(f"[INFO] Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table}")
        print()
        
        print("=" * 60)
        print("[SUCCESS] All connection tests passed!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print("[FAIL] Connection test failed!")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)
