"""
Simple script to add platform_id column to sessions table.
Run this to fix the database schema issue.
"""

import asyncio
import asyncpg
from app.config import settings
import sys

async def add_platform_id_column():
    """Add platform_id column to sessions table."""
    # Parse database URL
    db_url = settings.DATABASE_URL
    # Remove the +asyncpg part
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    print("=" * 60)
    print("Adding platform_id column to sessions table")
    print("=" * 60)
    print(f"Database: {db_url.split('@')[1] if '@' in db_url else db_url}")
    print()
    
    try:
        # Connect to database
        conn = await asyncpg.connect(db_url)
        print("[INFO] Connected to database")
        
        # Check if column exists
        check_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'sessions' AND column_name = 'platform_id'
        """
        result = await conn.fetch(check_query)
        
        if result:
            print("[INFO] platform_id column already exists")
            await conn.close()
            return True
        
        # Add the column
        print("[INFO] Adding platform_id column...")
        await conn.execute("""
            ALTER TABLE sessions 
            ADD COLUMN platform_id VARCHAR(50)
        """)
        print("[PASS] Column added successfully")
        
        # Populate from existing platform values
        print("[INFO] Populating platform_id from existing platform values...")
        result = await conn.execute("""
            UPDATE sessions 
            SET platform_id = platform 
            WHERE platform IS NOT NULL AND platform_id IS NULL
        """)
        print(f"[PASS] Populated platform_id for existing records")
        
        await conn.close()
        
        print()
        print("=" * 60)
        print("[SUCCESS] Migration completed successfully!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print("[FAIL] Migration failed!")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(add_platform_id_column())
    sys.exit(0 if result else 1)
