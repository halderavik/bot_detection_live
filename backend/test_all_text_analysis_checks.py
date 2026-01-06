"""
Comprehensive test script for all text analysis checks.

This script tests all 5 text analysis checks:
1. Gibberish detection
2. Copy-paste detection
3. Relevance analysis
4. Generic answer detection
5. Quality scoring

It creates questions and responses designed to trigger each check and verifies
that the system correctly identifies and flags problematic responses.
"""

import requests
import json
import sys
from typing import Dict, List, Tuple, Optional

# Production API URL
# BASE_URL = "https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1"

# Local development URL (uncomment to test locally)
BASE_URL = "http://localhost:8000/api/v1"


def check_api_health() -> bool:
    """
    Check if the API is accessible and healthy.
    
    Returns:
        bool: True if API is healthy, False otherwise
    """
    print("=" * 80)
    print("Checking API Health...")
    print("=" * 80)
    
    try:
        # Test main health endpoint
        health_url = BASE_URL.replace('/api/v1', '') if '/api/v1' in BASE_URL else BASE_URL
        health_response = requests.get(
            f"{health_url}/health",
            timeout=10
        )
        if health_response.status_code != 200:
            print(f"[FAIL] Health check failed: HTTP {health_response.status_code}")
            return False
        
        print("[PASS] Main API health check passed")
        
        # Test text-analysis health endpoint
        text_health_response = requests.get(
            f"{BASE_URL}/text-analysis/health",
            timeout=10
        )
        if text_health_response.status_code != 200:
            print(f"[FAIL] Text analysis health check failed: HTTP {text_health_response.status_code}")
            return False
        
        health_data = text_health_response.json()
        print(f"[PASS] Text analysis health check passed")
        print(f"   OpenAI Available: {health_data.get('openai_available', False)}")
        print(f"   Model: {health_data.get('model', 'N/A')}")
        
        if not health_data.get('openai_available', False):
            print("[WARNING] OpenAI is not available. Tests will use fallback analysis.")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] API health check failed: {e}")
        return False


def create_session() -> Optional[str]:
    """
    Create a new session for testing.
    
    Returns:
        Optional[str]: Session ID if successful, None otherwise
    """
    try:
        session_response = requests.post(
            f"{BASE_URL}/detection/sessions",
            params={"platform": "web"},
            headers={"User-Agent": "Mozilla/5.0 Test Client"},
            timeout=30
        )
        
        if session_response.status_code != 200:
            print(f"[FAIL] Failed to create session: HTTP {session_response.status_code}")
            print(f"Response: {session_response.text}")
            return None
        
        session_data = session_response.json()
        session_id = session_data["session_id"]
        print(f"[PASS] Session created: {session_id}")
        return session_id
        
    except Exception as e:
        print(f"[FAIL] Error creating session: {e}")
        return None


def submit_question(session_id: str, question_text: str) -> Optional[str]:
    """
    Submit a question for tracking.
    
    Args:
        session_id: Session ID
        question_text: Question text
        
    Returns:
        Optional[str]: Question ID if successful, None otherwise
    """
    try:
        question_response = requests.post(
            f"{BASE_URL}/text-analysis/questions",
            json={
                "session_id": session_id,
                "question_text": question_text,
                "question_type": "open_ended"
            },
            timeout=30
        )
        
        if question_response.status_code != 200:
            print(f"[FAIL] Failed to submit question: HTTP {question_response.status_code}")
            print(f"Response: {question_response.text}")
            return None
        
        question_data = question_response.json()
        question_id = question_data["question_id"]
        return question_id
        
    except Exception as e:
        print(f"[FAIL] Error submitting question: {e}")
        return None


def analyze_response(
    session_id: str,
    question_id: str,
    response_text: str
) -> Optional[Dict]:
    """
    Submit a response and get analysis results.
    
    Args:
        session_id: Session ID
        question_id: Question ID
        response_text: Response text to analyze
        
    Returns:
        Optional[Dict]: Analysis result if successful, None otherwise
    """
    try:
        response = requests.post(
            f"{BASE_URL}/text-analysis/responses",
            json={
                "session_id": session_id,
                "question_id": question_id,
                "response_text": response_text
            },
            timeout=60  # Longer timeout for OpenAI API calls
        )
        
        if response.status_code != 200:
            print(f"[FAIL] Failed to submit response: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        return response.json()
        
    except Exception as e:
        print(f"[FAIL] Error analyzing response: {e}")
        return None


def test_text_analysis_check(
    test_name: str,
    question: str,
    response: str,
    expected_flags: List[str],
    expected_quality_range: Tuple[float, float],
    check_description: str
) -> bool:
    """
    Test a single text analysis check.
    
    Args:
        test_name: Name of the test
        question: Question text
        response: Response text to analyze
        expected_flags: List of expected flag types
        expected_quality_range: Tuple of (min_quality, max_quality) expected
        check_description: Description of what this test checks
        
    Returns:
        bool: True if test passed, False otherwise
    """
    print("\n" + "=" * 80)
    print(f"TEST: {test_name}")
    print("=" * 80)
    print(f"Check: {check_description}")
    print(f"Question: {question}")
    print(f"Response: {response[:100]}{'...' if len(response) > 100 else ''}")
    print(f"Expected Flags: {expected_flags}")
    print(f"Expected Quality Range: {expected_quality_range[0]}-{expected_quality_range[1]}")
    
    # Create session
    session_id = create_session()
    if not session_id:
        return False
    
    # Submit question
    question_id = submit_question(session_id, question)
    if not question_id:
        return False
    
    # Analyze response
    result = analyze_response(session_id, question_id, response)
    if not result:
        return False
    
    # Extract results
    actual_flags = list(result.get("flag_reasons", {}).keys())
    quality_score = result.get("quality_score", 0)
    is_flagged = result.get("is_flagged", False)
    
    # Get detailed analysis
    analysis_details = result.get("analysis_details", {})
    gibberish_score = result.get("gibberish_score", 0)
    copy_paste_score = result.get("copy_paste_score", 0)
    relevance_score = result.get("relevance_score", 0)
    generic_score = result.get("generic_score", 0)
    
    print("\n" + "-" * 80)
    print("ANALYSIS RESULTS:")
    print("-" * 80)
    print(f"Quality Score: {quality_score}")
    print(f"Is Flagged: {is_flagged}")
    print(f"Actual Flags: {actual_flags}")
    print(f"\nDetailed Scores:")
    print(f"  Gibberish Score: {gibberish_score:.2f}")
    print(f"  Copy-Paste Score: {copy_paste_score:.2f}")
    print(f"  Relevance Score: {relevance_score:.2f}")
    print(f"  Generic Score: {generic_score:.2f}")
    
    if analysis_details:
        print(f"\nDetailed Analysis:")
        for check_type, check_result in analysis_details.items():
            if isinstance(check_result, dict):
                confidence = check_result.get("confidence", "N/A")
                reason = check_result.get("reason", "N/A")
                print(f"  {check_type}: confidence={confidence}, reason={reason[:100]}")
    
    # Verify results
    print("\n" + "-" * 80)
    print("VERIFICATION:")
    print("-" * 80)
    
    all_passed = True
    
    # Check flags
    if set(actual_flags) == set(expected_flags):
        print(f"[PASS] Flags match expected: {expected_flags}")
    else:
        print(f"[FAIL] Expected flags {expected_flags}, got {actual_flags}")
        all_passed = False
    
    # Check quality score range
    min_quality, max_quality = expected_quality_range
    if min_quality <= quality_score <= max_quality:
        print(f"[PASS] Quality score {quality_score} is in expected range [{min_quality}, {max_quality}]")
    else:
        print(f"[FAIL] Quality score {quality_score} is outside expected range [{min_quality}, {max_quality}]")
        all_passed = False
    
    # Check if flagged status matches expectations
    should_be_flagged = len(expected_flags) > 0
    if is_flagged == should_be_flagged:
        print(f"[PASS] Flagged status matches expectation: {is_flagged}")
    else:
        print(f"[FAIL] Expected flagged={should_be_flagged}, got {is_flagged}")
        all_passed = False
    
    return all_passed


def main():
    """Run all text analysis check tests."""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TEXT ANALYSIS CHECK TEST SUITE")
    print("=" * 80)
    print("\nThis script tests all 5 text analysis checks:")
    print("1. Gibberish Detection")
    print("2. Copy-Paste Detection")
    print("3. Relevance Analysis")
    print("4. Generic Answer Detection")
    print("5. Quality Scoring (with good response)")
    
    # Check API health first
    if not check_api_health():
        print("\n[FAIL] API health check failed. Cannot proceed with tests.")
        print("\nMake sure the backend server is running:")
        print("  cd backend")
        print("  python main.py")
        print("\nOr use Docker Compose:")
        print("  docker-compose up backend")
        sys.exit(1)
    
    # Define test cases
    test_cases = [
        {
            "test_name": "Gibberish Detection Test",
            "question": "What are your thoughts on customer service?",
            "response": "asdfghjkl qwertyuiop zxcvbnm 1234567890 !@#$%^&*()",
            "expected_flags": ["gibberish"],
            "expected_quality_range": (0, 30),
            "check_description": "Detects random character sequences and keyboard mashing"
        },
        {
            "test_name": "Copy-Paste Detection Test",
            "question": "How do you feel about our product?",
            "response": "Customer satisfaction is a fundamental metric that quantifies the degree to which a product or service meets or exceeds customer expectations. It is typically measured through various methodologies including surveys, feedback mechanisms, and Net Promoter Score (NPS) calculations.",
            "expected_flags": ["copy_paste"],
            "expected_quality_range": (20, 50),
            "check_description": "Detects formal, dictionary-style definitions that appear copied"
        },
        {
            "test_name": "Irrelevance Detection Test",
            "question": "What is your favorite color?",
            "response": "The weather today is really nice. I had pizza for lunch and it was delicious. Tomorrow I'm going to the movies.",
            "expected_flags": ["irrelevant"],
            "expected_quality_range": (10, 40),
            "check_description": "Detects responses that don't answer the question"
        },
        {
            "test_name": "Generic Answer Detection Test",
            "question": "What improvements would you suggest for our service?",
            "response": "idk",
            "expected_flags": ["generic"],
            "expected_quality_range": (0, 30),
            "check_description": "Detects low-effort, generic responses"
        },
        {
            "test_name": "High Quality Response Test",
            "question": "What features would you like to see in our product?",
            "response": "I would really appreciate a dark mode option for the interface, as I often work late at night and find bright screens tiring. Additionally, I think a keyboard shortcut customization feature would be great for power users like myself. Finally, better integration with calendar apps would help me manage my workflow more efficiently.",
            "expected_flags": [],
            "expected_quality_range": (70, 100),
            "check_description": "Validates that high-quality, thoughtful responses are not flagged"
        },
        {
            "test_name": "Mixed Issues Test - Gibberish + Generic",
            "question": "Tell us about your experience",
            "response": "asdfghjkl",
            "expected_flags": ["gibberish"],  # Gibberish takes priority over generic
            "expected_quality_range": (0, 20),
            "check_description": "Tests priority filtering (gibberish should take precedence)"
        },
        {
            "test_name": "Relevance Edge Case - Partial Answer",
            "question": "What is your favorite programming language?",
            "response": "I like computers and technology. Programming is interesting. Code is fun.",
            "expected_flags": ["irrelevant"],  # May or may not be flagged, but should be low quality
            "expected_quality_range": (20, 60),
            "check_description": "Tests detection of partially relevant but vague responses"
        },
        {
            "test_name": "Copy-Paste from Wikipedia Test",
            "question": "What is artificial intelligence?",
            "response": "Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of 'intelligent agents': any device that perceives its environment and takes actions that maximize its chance of achieving its goals.",
            "expected_flags": ["copy_paste"],
            "expected_quality_range": (30, 60),
            "check_description": "Detects Wikipedia-style definitions that are clearly copied"
        }
    ]
    
    # Run all tests
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'#' * 80}")
        print(f"TEST {i}/{len(test_cases)}")
        print(f"{'#' * 80}")
        
        passed = test_text_analysis_check(**test_case)
        results.append({
            "test_name": test_case["test_name"],
            "passed": passed
        })
        
        if not passed:
            print(f"\n[WARNING] Test '{test_case['test_name']}' had issues. Review the results above.")
    
    # Print summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)
    
    print(f"\nTotal Tests: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print(f"Success Rate: {(passed_count / total_count * 100):.1f}%")
    
    print("\n" + "-" * 80)
    print("DETAILED RESULTS:")
    print("-" * 80)
    
    for result in results:
        status = "[PASS]" if result["passed"] else "[FAIL]"
        print(f"{status} - {result['test_name']}")
    
    # Final verdict
    print("\n" + "=" * 80)
    if passed_count == total_count:
        print("SUCCESS: ALL TESTS PASSED!")
        print("=" * 80)
        sys.exit(0)
    else:
        print(f"WARNING: {total_count - passed_count} TEST(S) HAD ISSUES")
        print("=" * 80)
        print("\nReview the detailed results above to identify any problems.")
        sys.exit(1)


if __name__ == "__main__":
    main()
