#!/usr/bin/env python3
"""
Production API test for ChatGPT text classification capabilities.

This script tests the deployed production API to validate ChatGPT's ability
to correctly classify different types of problematic text.
"""

import requests
import json
import time
from typing import List, Dict, Any

class ProductionClassificationTester:
    """Test ChatGPT classification via production API."""
    
    def __init__(self, base_url: str = "https://bot-backend-119522247395.northamerica-northeast2.run.app"):
        self.base_url = base_url
        self.session_id = None
        self.question_id = None
        self.test_cases = self._create_test_cases()
        self.results = []
    
    def _create_test_cases(self) -> List[Dict[str, Any]]:
        """Create comprehensive test cases for different text problems."""
        return [
            # Gibberish test cases
            {
                "category": "gibberish",
                "question": "What is your favorite color?",
                "text": "asdfghjkl qwertyuiop zxcvbnm",
                "expected_flags": ["gibberish"],
                "expected_quality_range": (0, 30)
            },
            {
                "category": "gibberish",
                "question": "How do you feel about our product?",
                "text": "kjhgfdsa mnbvcxz poiuytr",
                "expected_flags": ["gibberish"],
                "expected_quality_range": (0, 30)
            },
            
            # Copy-paste test cases
            {
                "category": "copy_paste",
                "question": "What is your favorite color?",
                "text": "Blue is a color that is associated with tranquility, stability, and trust. It is often used in corporate branding and is considered one of the most popular colors worldwide. The color blue has been scientifically proven to have calming effects on the human psyche.",
                "expected_flags": ["copy_paste"],
                "expected_quality_range": (30, 60)
            },
            {
                "category": "copy_paste",
                "question": "How was your experience?",
                "text": "Our company is committed to providing exceptional customer service and maintaining the highest standards of quality. We strive to exceed customer expectations through innovative solutions and dedicated support.",
                "expected_flags": ["copy_paste"],
                "expected_quality_range": (30, 60)
            },
            
            # Irrelevant test cases
            {
                "category": "irrelevant",
                "question": "What is your favorite color?",
                "text": "I like pizza and movies",
                "expected_flags": ["irrelevant"],
                "expected_quality_range": (0, 40)
            },
            {
                "category": "irrelevant",
                "question": "How do you rate our service?",
                "text": "The weather is nice today",
                "expected_flags": ["irrelevant"],
                "expected_quality_range": (0, 40)
            },
            
            # Generic test cases
            {
                "category": "generic",
                "question": "What is your favorite color?",
                "text": "idk",
                "expected_flags": ["generic"],
                "expected_quality_range": (0, 30)
            },
            {
                "category": "generic",
                "question": "How was your experience?",
                "text": "good",
                "expected_flags": ["generic"],
                "expected_quality_range": (0, 30)
            },
            {
                "category": "generic",
                "question": "What do you think about our product?",
                "text": "fine",
                "expected_flags": ["generic"],
                "expected_quality_range": (0, 30)
            },
            
            # High quality test cases
            {
                "category": "high_quality",
                "question": "What is your favorite color?",
                "text": "My favorite color is blue because it reminds me of the ocean and sky. It has a calming effect and I find it very peaceful.",
                "expected_flags": [],
                "expected_quality_range": (70, 100)
            },
            {
                "category": "high_quality",
                "question": "How was your experience with our service?",
                "text": "I had a great experience with your service. The staff was friendly and helpful, and the process was quick and efficient. I would definitely recommend it to others.",
                "expected_flags": [],
                "expected_quality_range": (70, 100)
            },
            {
                "category": "high_quality",
                "question": "What improvements would you suggest?",
                "text": "I think the service could be improved by adding more payment options and extending the hours of operation. The current system works well, but these changes would make it even better.",
                "expected_flags": [],
                "expected_quality_range": (70, 100)
            },
            
            # Mixed quality test cases
            {
                "category": "mixed_quality",
                "question": "What is your favorite color?",
                "text": "Blue is nice I guess",
                "expected_flags": [],
                "expected_quality_range": (40, 70)
            },
            {
                "category": "mixed_quality",
                "question": "How was your experience?",
                "text": "It was okay, nothing special but not bad either",
                "expected_flags": [],
                "expected_quality_range": (40, 70)
            }
        ]
    
    def create_session(self) -> bool:
        """Create a new session for testing."""
        try:
            response = requests.post(f"{self.base_url}/api/v1/detection/sessions")
            if response.status_code == 200:
                data = response.json()
                self.session_id = data["session_id"]
                print(f"✅ Created session: {self.session_id}")
                return True
            else:
                print(f"❌ Failed to create session: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error creating session: {e}")
            return False
    
    def submit_question(self, question_text: str) -> bool:
        """Submit a question and get question_id."""
        if not self.session_id:
            print("❌ No session ID available")
            return False
        
        try:
            data = {
                "session_id": self.session_id,
                "question_text": question_text,
                "question_type": "open_ended"
            }
            response = requests.post(
                f"{self.base_url}/api/v1/text-analysis/questions",
                json=data
            )
            if response.status_code == 200:
                result = response.json()
                self.question_id = result["question_id"]
                return True
            else:
                print(f"❌ Failed to submit question: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error submitting question: {e}")
            return False
    
    def submit_response(self, response_text: str) -> Dict[str, Any]:
        """Submit a response and get analysis results."""
        if not self.session_id or not self.question_id:
            return {"error": "No session or question ID available"}
        
        try:
            data = {
                "session_id": self.session_id,
                "question_id": self.question_id,
                "response_text": response_text
            }
            response = requests.post(
                f"{self.base_url}/api/v1/text-analysis/responses",
                json=data
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": str(e)}
    
    def run_tests(self) -> Dict[str, Any]:
        """Run all classification tests."""
        print("🧪 Starting ChatGPT Text Classification Tests (Production API)")
        print(f"📊 Testing {len(self.test_cases)} different text scenarios")
        print(f"🌐 API Base URL: {self.base_url}")
        print("=" * 60)
        
        # Create session
        if not self.create_session():
            return {"error": "Failed to create session"}
        
        total_tests = len(self.test_cases)
        correct_classifications = 0
        category_results = {}
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n🔍 Test {i}/{total_tests}: {test_case['category']}")
            print(f"Question: {test_case['question']}")
            print(f"Text: {test_case['text'][:100]}{'...' if len(test_case['text']) > 100 else ''}")
            
            # Submit question
            if not self.submit_question(test_case['question']):
                print("❌ Failed to submit question")
                continue
            
            # Submit response
            result = self.submit_response(test_case['text'])
            
            if "error" in result:
                print(f"❌ ERROR: {result['error']}")
                continue
            
            # Check if classification is correct
            is_correct = self._evaluate_result(test_case, result)
            
            if is_correct:
                correct_classifications += 1
                print("✅ CORRECT")
            else:
                print("❌ INCORRECT")
            
            # Store results
            test_result = {
                "test_case": test_case,
                "result": result,
                "is_correct": is_correct
            }
            self.results.append(test_result)
            
            # Track by category
            category = test_case['category']
            if category not in category_results:
                category_results[category] = {"total": 0, "correct": 0}
            category_results[category]["total"] += 1
            if is_correct:
                category_results[category]["correct"] += 1
            
            # Print detailed results
            print(f"   Quality Score: {result.get('quality_score', 'N/A')}")
            print(f"   Flagged: {result.get('is_flagged', 'N/A')}")
            print(f"   Flags: {list(result.get('flag_reasons', {}).keys())}")
            print(f"   Expected Flags: {test_case['expected_flags']}")
            print(f"   Expected Quality Range: {test_case['expected_quality_range']}")
            
            # Small delay to avoid rate limiting
            time.sleep(1)
        
        # Calculate overall accuracy
        accuracy = (correct_classifications / total_tests) * 100 if total_tests > 0 else 0
        
        # Calculate category accuracies
        category_accuracies = {}
        for category, stats in category_results.items():
            category_accuracies[category] = (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        
        return {
            "total_tests": total_tests,
            "correct_classifications": correct_classifications,
            "accuracy": accuracy,
            "category_results": category_results,
            "category_accuracies": category_accuracies,
            "detailed_results": self.results
        }
    
    def _evaluate_result(self, test_case: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Evaluate if the classification result is correct."""
        expected_flags = set(test_case['expected_flags'])
        actual_flags = set(result.get('flag_reasons', {}).keys())
        
        # Check if flags match
        flags_correct = expected_flags == actual_flags
        
        # Check if quality score is in expected range
        quality_score = result.get('quality_score', 0)
        quality_min, quality_max = test_case['expected_quality_range']
        quality_correct = quality_min <= quality_score <= quality_max
        
        # For high quality responses, also check that they're not flagged
        if test_case['category'] == 'high_quality':
            return flags_correct and quality_correct and not result.get('is_flagged', False)
        
        # For other categories, flags and quality should match
        return flags_correct and quality_correct
    
    def print_summary(self, results: Dict[str, Any]):
        """Print a comprehensive summary of test results."""
        print("\n" + "=" * 60)
        print("📈 CHATGPT TEXT CLASSIFICATION TEST RESULTS")
        print("=" * 60)
        
        if "error" in results:
            print(f"❌ Test failed: {results['error']}")
            return
        
        print(f"\n🎯 Overall Accuracy: {results['accuracy']:.1f}%")
        print(f"✅ Correct Classifications: {results['correct_classifications']}/{results['total_tests']}")
        
        print(f"\n📊 Category Breakdown:")
        for category, accuracy in results['category_accuracies'].items():
            stats = results['category_results'][category]
            print(f"   {category.replace('_', ' ').title()}: {accuracy:.1f}% ({stats['correct']}/{stats['total']})")
        
        print(f"\n🔍 Detailed Analysis:")
        
        # Analyze common misclassifications
        incorrect_results = [r for r in results['detailed_results'] if not r['is_correct']]
        if incorrect_results:
            print(f"   ❌ Misclassified Cases: {len(incorrect_results)}")
            for result in incorrect_results[:3]:  # Show first 3
                test_case = result['test_case']
                print(f"      - {test_case['category']}: '{test_case['text'][:50]}...'")
        else:
            print("   ✅ All classifications were correct!")
        
        # Performance insights
        print(f"\n💡 Performance Insights:")
        if results['accuracy'] >= 90:
            print("   🎉 Excellent classification performance!")
        elif results['accuracy'] >= 80:
            print("   👍 Good classification performance")
        elif results['accuracy'] >= 70:
            print("   ⚠️  Moderate classification performance - consider prompt tuning")
        else:
            print("   🚨 Poor classification performance - needs improvement")
        
        # Category-specific insights
        print(f"\n📋 Category-Specific Insights:")
        for category, accuracy in results['category_accuracies'].items():
            if accuracy >= 90:
                status = "🎯 Excellent"
            elif accuracy >= 80:
                status = "👍 Good"
            elif accuracy >= 70:
                status = "⚠️  Moderate"
            else:
                status = "🚨 Needs Improvement"
            print(f"   {category.replace('_', ' ').title()}: {status} ({accuracy:.1f}%)")

def main():
    """Main test execution function."""
    print("🤖 ChatGPT Text Classification Test Suite (Production)")
    print("Testing OpenAI GPT-4o-mini model's text analysis capabilities via production API")
    print("=" * 60)
    
    # Run tests
    tester = ProductionClassificationTester()
    results = tester.run_tests()
    
    # Print summary
    tester.print_summary(results)
    
    # Save detailed results
    with open('production_classification_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: production_classification_results.json")
    
    return results

if __name__ == "__main__":
    main()
