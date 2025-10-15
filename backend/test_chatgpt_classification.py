#!/usr/bin/env python3
"""
Comprehensive test script for ChatGPT text classification capabilities.

This script tests the OpenAI GPT-4o-mini model's ability to correctly classify
different types of problematic text including gibberish, copy-paste, irrelevant,
generic, and high-quality responses.
"""

import asyncio
import json
import sys
import os
from typing import List, Dict, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.text_analysis_service import text_analysis_service

class TextClassificationTester:
    """Test ChatGPT's text classification capabilities."""
    
    def __init__(self):
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
            {
                "category": "gibberish",
                "text": "1234567890 !@#$%^&*()",
                "question": "What is your opinion?",
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
            {
                "category": "irrelevant",
                "question": "What improvements would you suggest?",
                "text": "I have a dog named Max",
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
            {
                "category": "generic",
                "question": "Any additional comments?",
                "text": "nothing",
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
    
    async def run_tests(self) -> Dict[str, Any]:
        """Run all classification tests."""
        print("🧪 Starting ChatGPT Text Classification Tests...")
        print(f"📊 Testing {len(self.test_cases)} different text scenarios")
        print("=" * 60)
        
        total_tests = len(self.test_cases)
        correct_classifications = 0
        category_results = {}
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n🔍 Test {i}/{total_tests}: {test_case['category']}")
            print(f"Question: {test_case['question']}")
            print(f"Text: {test_case['text'][:100]}{'...' if len(test_case['text']) > 100 else ''}")
            
            try:
                # Run the analysis
                result = await text_analysis_service.analyze_response(
                    test_case['question'],
                    test_case['text']
                )
                
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
                    "result": {
                        "quality_score": result.quality_score,
                        "is_flagged": result.is_flagged,
                        "flag_reasons": list(result.flag_reasons.keys()),
                        "gibberish_score": result.gibberish_score,
                        "copy_paste_score": result.copy_paste_score,
                        "relevance_score": result.relevance_score,
                        "generic_score": result.generic_score,
                        "confidence": result.confidence
                    },
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
                print(f"   Quality Score: {result.quality_score}")
                print(f"   Flagged: {result.is_flagged}")
                print(f"   Flags: {list(result.flag_reasons.keys())}")
                print(f"   Expected Flags: {test_case['expected_flags']}")
                print(f"   Expected Quality Range: {test_case['expected_quality_range']}")
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
                test_result = {
                    "test_case": test_case,
                    "error": str(e),
                    "is_correct": False
                }
                self.results.append(test_result)
        
        # Calculate overall accuracy
        accuracy = (correct_classifications / total_tests) * 100
        
        # Calculate category accuracies
        category_accuracies = {}
        for category, stats in category_results.items():
            category_accuracies[category] = (stats["correct"] / stats["total"]) * 100
        
        return {
            "total_tests": total_tests,
            "correct_classifications": correct_classifications,
            "accuracy": accuracy,
            "category_results": category_results,
            "category_accuracies": category_accuracies,
            "detailed_results": self.results
        }
    
    def _evaluate_result(self, test_case: Dict[str, Any], result) -> bool:
        """Evaluate if the classification result is correct."""
        expected_flags = set(test_case['expected_flags'])
        actual_flags = set(result.flag_reasons.keys())
        
        # Check if flags match
        flags_correct = expected_flags == actual_flags
        
        # Check if quality score is in expected range
        quality_min, quality_max = test_case['expected_quality_range']
        quality_correct = quality_min <= result.quality_score <= quality_max
        
        # For high quality responses, also check that they're not flagged
        if test_case['category'] == 'high_quality':
            return flags_correct and quality_correct and not result.is_flagged
        
        # For other categories, flags and quality should match
        return flags_correct and quality_correct
    
    def print_summary(self, results: Dict[str, Any]):
        """Print a comprehensive summary of test results."""
        print("\n" + "=" * 60)
        print("📈 CHATGPT TEXT CLASSIFICATION TEST RESULTS")
        print("=" * 60)
        
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

async def main():
    """Main test execution function."""
    print("🤖 ChatGPT Text Classification Test Suite")
    print("Testing OpenAI GPT-4o-mini model's text analysis capabilities")
    print("=" * 60)
    
    # Check if OpenAI is available
    if not text_analysis_service.openai_service.is_available:
        print("❌ OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
        print("   The test will run in fallback mode (not recommended for classification testing).")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    # Run tests
    tester = TextClassificationTester()
    results = await tester.run_tests()
    
    # Print summary
    tester.print_summary(results)
    
    # Save detailed results
    with open('chatgpt_classification_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: chatgpt_classification_results.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
