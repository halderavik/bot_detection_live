import psycopg2
import os
import sys

def verify_schema():
    """Verify database schema using psycopg2."""
    # Get credentials from DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        return False
    
    import re
    match = re.search(r'postgresql\+asyncpg://([^:]+):([^@]+)@/([^?]+)', db_url)
    if not match:
        print("ERROR: Could not parse DATABASE_URL")
        return False
    
    user, password, database = match.groups()
    host = os.getenv("CLOUD_SQL_IP", "34.130.49.170")
    port = 5432
    
    try:
        conn = psycopg2.connect(host=host, port=port, database=database, user=user, password=password)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
        tables = [row[0] for row in cursor.fetchall()]
        required = ['sessions', 'behavior_data', 'detection_results', 'survey_questions', 'survey_responses', 'fraud_indicators']
        
        print(f"\nFound {len(tables)} tables:")
        for table in tables:
            print(f"  [OK] {table}")
        
        missing = [t for t in required if t not in tables]
        if missing:
            print(f"\n[ERROR] Missing tables: {missing}")
            return False
        
        print(f"\n[OK] All {len(required)} required tables exist")
        
        # Check platform_id in sessions
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='sessions' AND column_name='platform_id'")
        if cursor.fetchone():
            print("[OK] platform_id column exists in sessions")
        else:
            print("[ERROR] platform_id column missing")
            return False
        
        # Check device_fingerprint in sessions
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='sessions' AND column_name='device_fingerprint'")
        if cursor.fetchone():
            print("[OK] device_fingerprint column exists in sessions")
        else:
            print("[ERROR] device_fingerprint column missing")
            return False
        
        # Check fraud_indicators table
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='fraud_indicators' ORDER BY column_name")
        fraud_cols = [row[0] for row in cursor.fetchall()]
        required_fraud_cols = ['survey_id', 'platform_id', 'respondent_id', 'overall_fraud_score']
        
        for col in required_fraud_cols:
            if col in fraud_cols:
                print(f"[OK] {col} exists in fraud_indicators")
            else:
                print(f"[ERROR] {col} missing in fraud_indicators")
                return False
        
        # Check detection_results fraud columns
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='detection_results' AND column_name IN ('fraud_score', 'fraud_indicators')")
        fraud_dr_cols = [row[0] for row in cursor.fetchall()]
        if 'fraud_score' in fraud_dr_cols and 'fraud_indicators' in fraud_dr_cols:
            print("[OK] fraud_score and fraud_indicators exist in detection_results")
        else:
            print("[ERROR] Missing fraud columns in detection_results")
            return False
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("[OK] Schema verification complete - All checks passed!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = verify_schema()
    sys.exit(0 if result else 1)
