"""
Test API connection and database via HTTP endpoints.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_connection():
    """Test API and database connection."""
    print("=" * 60)
    print("Testing API and Database Connection")
    print("=" * 60)
    print()
    
    # Test 1: Health endpoint
    print("Test 1: Health endpoint...")
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        if response.status_code == 200:
            print("[PASS] Health endpoint is accessible")
            print(f"      Response: {response.json()}")
        else:
            print(f"[FAIL] Health endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Health endpoint error: {e}")
        return False
    print()
    
    # Test 2: Text analysis health
    print("Test 2: Text analysis health...")
    try:
        response = requests.get(f"{BASE_URL}/text-analysis/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("[PASS] Text analysis health check passed")
            print(f"      OpenAI Available: {data.get('openai_available', False)}")
            print(f"      Model: {data.get('model', 'N/A')}")
        else:
            print(f"[FAIL] Text analysis health returned {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Text analysis health error: {e}")
        return False
    print()
    
    # Test 3: Create session (tests database)
    print("Test 3: Creating session (database test)...")
    try:
        response = requests.post(
            f"{BASE_URL}/detection/sessions",
            params={"platform": "web"},
            headers={"User-Agent": "Connection Test"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            session_id = data.get("session_id")
            print(f"[PASS] Session created successfully!")
            print(f"      Session ID: {session_id}")
            print(f"      Created at: {data.get('created_at', 'N/A')}")
            return True
        else:
            print(f"[FAIL] Session creation returned {response.status_code}")
            print(f"      Response: {response.text}")
            return False
    except Exception as e:
        print(f"[FAIL] Session creation error: {e}")
        return False

if __name__ == "__main__":
    print()
    success = test_connection()
    print()
    print("=" * 60)
    if success:
        print("[SUCCESS] All connection tests passed!")
        print("Database is working correctly!")
    else:
        print("[FAIL] Connection tests failed!")
        print("Check the error messages above.")
    print("=" * 60)
    exit(0 if success else 1)
