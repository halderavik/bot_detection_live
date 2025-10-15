"""
Test script to validate improved text classification performance.

This script tests the deployed backend to ensure:
1. Relevance detection is working correctly
2. Priority-based flag filtering prevents over-flagging
3. Classification accuracy has improved
"""

import requests
import json
import sys

# Production API URL
BASE_URL = "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1"

def check_api_health():
    """Check if the API is accessible and healthy."""
    print("Checking API health...")
    try:
        # Test health endpoint
        health_response = requests.get(
            f"https://bot-backend-119522247395.northamerica-northeast2.run.app/health",
            timeout=10
        )
        if health_response.status_code != 200:
            print(f"FAIL - Health check failed: HTTP {health_response.status_code}")
            return False
        
        print("SUCCESS - API health check passed")
        
        # Test text-analysis health endpoint
        health_response = requests.get(f"{BASE_URL}/text-analysis/health", timeout=10)
        if health_response.status_code != 200:
            print(f"FAIL - Text analysis health check failed: HTTP {health_response.status_code}")
            print(f"Response: {health_response.text}")
            return False
        
        health_data = health_response.json()
        print(f"SUCCESS - Text analysis health: {health_data}")
        
        # Test text-analysis stats endpoint
        stats_response = requests.get(f"{BASE_URL}/text-analysis/stats", timeout=10)
        if stats_response.status_code != 200:
            print(f"FAIL - Text analysis stats endpoint check failed: HTTP {stats_response.status_code}")
            print(f"Response: {stats_response.text}")
            return False
        
        print("SUCCESS - Text analysis endpoints are accessible")
        return True
        
    except Exception as e:
        print(f"FAIL - API health check failed: {e}")
        return False

def test_classification(question: str, answer: str, expected_flags: list, test_name: str):
    """Test a single classification case."""
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"Question: {question}")
    print(f"Answer: {answer}")
    print(f"Expected flags: {expected_flags}")
    
    try:
        # Step 0: Create a session first (using bot detection endpoint)
        session_response = requests.post(
            f"{BASE_URL}/detection/sessions",
            params={"platform": "web"},
            headers={"User-Agent": "Mozilla/5.0 Test"},
            timeout=30
        )
        
        if session_response.status_code != 200:
            print(f"FAIL - Failed to create session: HTTP {session_response.status_code}")
            print(f"Response: {session_response.text}")
            return False
        
        session_data = session_response.json()
        session_id = session_data["session_id"]
        
        # Step 1: Submit question
        question_response = requests.post(
            f"{BASE_URL}/text-analysis/questions",
            json={
                "session_id": session_id,
                "question_text": question,
                "question_type": "open_ended"
            },
            timeout=30
        )
        
        if question_response.status_code != 200:
            print(f"FAIL - Failed to submit question: HTTP {question_response.status_code}")
            print(f"Response: {question_response.text}")
            return False
        
        question_data = question_response.json()
        question_id = question_data["question_id"]
        
        # Step 2: Submit response
        response_response = requests.post(
            f"{BASE_URL}/text-analysis/responses",
            json={
                "session_id": session_id,
                "question_id": question_id,
                "response_text": answer
            },
            timeout=30
        )
        
        if response_response.status_code != 200:
            print(f"FAIL - Failed to submit response: HTTP {response_response.status_code}")
            print(f"Response: {response_response.text}")
            return False
        
        result = response_response.json()
        print(f"DEBUG - Full response: {json.dumps(result, indent=2)}")
        
        # Get flags directly from the response (not nested under "analysis")
        actual_flags = list(result.get("flag_reasons", {}).keys())
        
        print(f"Actual flags: {actual_flags}")
        print(f"Quality score: {result.get('quality_score', 'N/A')}")
        print(f"Is flagged: {result.get('is_flagged', False)}")
        
        # Check if actual flags match expected flags
        if set(actual_flags) == set(expected_flags):
            print("PASS - Flags match expected")
            return True
        else:
            print(f"FAIL - Expected {expected_flags}, got {actual_flags}")
            return False
            
    except Exception as e:
        print(f"FAIL - Error: {e}")
        return False

def main():
    """Run all classification tests."""
    print("Testing Improved Text Classification")
    print("="*60)
    
    # Check API health first
    if not check_api_health():
        print("\nFAIL - API health check failed. Cannot proceed with tests.")
        sys.exit(1)
    
    tests = [
        {
            "question": "What is your favorite color?",
            "answer": "asdfghjkl qwertyuiop zxcvbnm",
            "expected_flags": ["gibberish", "irrelevant"],
            "test_name": "Gibberish Detection (should flag gibberish and irrelevant)"
        },
        {
            "question": "What is your favorite color?",
            "answer": "Blue is a color that is associated with tranquility, stability, and trust. It is often used in corporate branding and is considered one of the most popular colors worldwide.",
            "expected_flags": ["copy_paste"],
            "test_name": "Copy-Paste Detection"
        },
        {
            "question": "What is your favorite color?",
            "answer": "I like pizza and movies",
            "expected_flags": ["irrelevant", "low_quality"],
            "test_name": "Irrelevant Detection (should flag irrelevant and low quality)"
        },
        {
            "question": "What is your favorite color?",
            "answer": "idk",
            "expected_flags": ["irrelevant", "low_quality"],
            "test_name": "Generic Detection (prioritizes irrelevant over generic)"
        },
        {
            "question": "What is your favorite color?",
            "answer": "My favorite color is blue because it reminds me of the ocean and the sky. It makes me feel calm and peaceful.",
            "expected_flags": [],
            "test_name": "High-Quality Response (should not be flagged)"
        }
    ]
    
    results = []
    for test in tests:
        result = test_classification(
            test["question"],
            test["answer"],
            test["expected_flags"],
            test["test_name"]
        )
        results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    passed = sum(results)
    total = len(results)
    accuracy = (passed / total) * 100 if total > 0 else 0
    
    print(f"Passed: {passed}/{total}")
    print(f"Accuracy: {accuracy:.1f}%")
    
    if accuracy >= 80:
        print("SUCCESS - Classification accuracy is acceptable (>=80%)")
    else:
        print("NEEDS IMPROVEMENT - Classification accuracy is below target")
    
    return accuracy >= 80

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

