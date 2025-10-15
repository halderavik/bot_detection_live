#!/usr/bin/env python3
"""
Simple production API test for ChatGPT text classification.
"""

import requests
import json
import time

def test_chatgpt_classification():
    """Test ChatGPT classification via production API."""
    base_url = "https://bot-backend-119522247395.northamerica-northeast2.run.app"
    
    print("Testing ChatGPT Text Classification via Production API")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "category": "gibberish",
            "question": "What is your favorite color?",
            "text": "asdfghjkl qwertyuiop zxcvbnm",
            "expected_flags": ["gibberish"]
        },
        {
            "category": "copy_paste",
            "question": "What is your favorite color?",
            "text": "Blue is a color that is associated with tranquility, stability, and trust. It is often used in corporate branding and is considered one of the most popular colors worldwide.",
            "expected_flags": ["copy_paste"]
        },
        {
            "category": "irrelevant",
            "question": "What is your favorite color?",
            "text": "I like pizza and movies",
            "expected_flags": ["irrelevant"]
        },
        {
            "category": "generic",
            "question": "What is your favorite color?",
            "text": "idk",
            "expected_flags": ["generic"]
        },
        {
            "category": "high_quality",
            "question": "What is your favorite color?",
            "text": "My favorite color is blue because it reminds me of the ocean and sky. It has a calming effect and I find it very peaceful.",
            "expected_flags": []
        }
    ]
    
    # Create session
    print("Creating session...")
    session_response = requests.post(f"{base_url}/api/v1/detection/sessions")
    if session_response.status_code != 200:
        print(f"Failed to create session: {session_response.status_code}")
        return
    
    session_id = session_response.json()["session_id"]
    print(f"Session created: {session_id}")
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['category']}")
        print(f"Question: {test_case['question']}")
        print(f"Text: {test_case['text'][:50]}...")
        
        # Submit question
        question_data = {
            "session_id": session_id,
            "question_text": test_case['question'],
            "question_type": "open_ended"
        }
        question_response = requests.post(
            f"{base_url}/api/v1/text-analysis/questions",
            json=question_data
        )
        
        if question_response.status_code != 200:
            print(f"Failed to submit question: {question_response.status_code}")
            continue
        
        question_id = question_response.json()["question_id"]
        
        # Submit response
        response_data = {
            "session_id": session_id,
            "question_id": question_id,
            "response_text": test_case['text']
        }
        response = requests.post(
            f"{base_url}/api/v1/text-analysis/responses",
            json=response_data
        )
        
        if response.status_code != 200:
            print(f"Failed to submit response: {response.status_code}")
            continue
        
        result = response.json()
        
        # Analyze results
        actual_flags = list(result.get('flag_reasons', {}).keys())
        expected_flags = test_case['expected_flags']
        
        is_correct = set(actual_flags) == set(expected_flags)
        
        print(f"Quality Score: {result.get('quality_score', 'N/A')}")
        print(f"Flagged: {result.get('is_flagged', 'N/A')}")
        print(f"Actual Flags: {actual_flags}")
        print(f"Expected Flags: {expected_flags}")
        print(f"Correct: {'YES' if is_correct else 'NO'}")
        
        results.append({
            "test_case": test_case,
            "result": result,
            "is_correct": is_correct
        })
        
        time.sleep(1)  # Rate limiting
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    correct = sum(1 for r in results if r['is_correct'])
    total = len(results)
    accuracy = (correct / total) * 100 if total > 0 else 0
    
    print(f"Overall Accuracy: {accuracy:.1f}%")
    print(f"Correct: {correct}/{total}")
    
    # Category breakdown
    categories = {}
    for result in results:
        category = result['test_case']['category']
        if category not in categories:
            categories[category] = {'total': 0, 'correct': 0}
        categories[category]['total'] += 1
        if result['is_correct']:
            categories[category]['correct'] += 1
    
    print("\nCategory Breakdown:")
    for category, stats in categories.items():
        cat_accuracy = (stats['correct'] / stats['total']) * 100
        print(f"  {category}: {cat_accuracy:.1f}% ({stats['correct']}/{stats['total']})")
    
    # Save results
    with open('classification_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: classification_test_results.json")

if __name__ == "__main__":
    test_chatgpt_classification()
