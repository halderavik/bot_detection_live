#!/usr/bin/env python3
"""
Test a single request to debug the OpenAI integration.
"""

import requests
import json

def test_single_request():
    """Test a single text analysis request."""
    base_url = "https://bot-backend-119522247395.northamerica-northeast2.run.app"
    
    print("Testing single text analysis request...")
    
    # Create session
    session_response = requests.post(f"{base_url}/api/v1/detection/sessions")
    if session_response.status_code != 200:
        print(f"Failed to create session: {session_response.status_code}")
        return
    
    session_id = session_response.json()["session_id"]
    print(f"Session created: {session_id}")
    
    # Submit question
    question_data = {
        "session_id": session_id,
        "question_text": "What is your favorite color?",
        "question_type": "open_ended"
    }
    question_response = requests.post(
        f"{base_url}/api/v1/text-analysis/questions",
        json=question_data
    )
    
    if question_response.status_code != 200:
        print(f"Failed to submit question: {question_response.status_code}")
        return
    
    question_id = question_response.json()["question_id"]
    print(f"Question submitted: {question_id}")
    
    # Submit response with gibberish text
    response_data = {
        "session_id": session_id,
        "question_id": question_id,
        "response_text": "asdfghjkl qwertyuiop zxcvbnm"
    }
    response = requests.post(
        f"{base_url}/api/v1/text-analysis/responses",
        json=response_data
    )
    
    if response.status_code != 200:
        print(f"Failed to submit response: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    result = response.json()
    print(f"Analysis result:")
    print(f"  Quality Score: {result.get('quality_score', 'N/A')}")
    print(f"  Flagged: {result.get('is_flagged', 'N/A')}")
    print(f"  Flags: {list(result.get('flag_reasons', {}).keys())}")
    print(f"  Gibberish Score: {result.get('gibberish_score', 'N/A')}")
    print(f"  Copy-paste Score: {result.get('copy_paste_score', 'N/A')}")
    print(f"  Relevance Score: {result.get('relevance_score', 'N/A')}")
    print(f"  Generic Score: {result.get('generic_score', 'N/A')}")
    print(f"  Confidence: {result.get('confidence', 'N/A')}")
    print(f"  Analysis Details: {result.get('analysis_details', {})}")
    
    # Check if it's using fallback mode
    if result.get('quality_score') == 50.0 and not result.get('is_flagged'):
        print("\nWARNING: This appears to be fallback mode (quality score 50, no flags)")
    else:
        print("\nSUCCESS: This appears to be using real OpenAI analysis!")

if __name__ == "__main__":
    test_single_request()
