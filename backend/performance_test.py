"""
Performance Testing Suite for Bot Detection API

This script provides comprehensive performance testing for the bot detection API
including load testing, stress testing, and benchmarking of key endpoints.
"""

import asyncio
import aiohttp
import time
import statistics
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import argparse

class APIPerformanceTester:
    """Performance testing class for Bot Detection API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.results = []
        self.session_ids = []
        
    async def test_health_endpoint(self, iterations: int = 100) -> Dict[str, Any]:
        """Test the health endpoint performance."""
        print(f"🔍 Testing health endpoint ({iterations} requests)...")
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            response_times = []
            errors = 0
            
            for i in range(iterations):
                request_start = time.time()
                try:
                    async with session.get(f"{self.base_url}/health") as response:
                        if response.status == 200:
                            response_time = (time.time() - request_start) * 1000
                            response_times.append(response_time)
                        else:
                            errors += 1
                except Exception as e:
                    errors += 1
                    print(f"Error in health test {i}: {e}")
            
            total_time = time.time() - start_time
            
            return {
                "endpoint": "health",
                "iterations": iterations,
                "total_time": total_time,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "median_response_time": statistics.median(response_times) if response_times else 0,
                "requests_per_second": iterations / total_time,
                "errors": errors,
                "success_rate": ((iterations - errors) / iterations) * 100
            }
    
    async def test_session_creation(self, iterations: int = 50) -> Dict[str, Any]:
        """Test session creation endpoint performance."""
        print(f"🔍 Testing session creation ({iterations} requests)...")
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            response_times = []
            errors = 0
            
            for i in range(iterations):
                request_start = time.time()
                try:
                    async with session.post(f"{self.api_base}/detection/sessions") as response:
                        if response.status == 200:
                            data = await response.json()
                            self.session_ids.append(data.get('session_id'))
                            response_time = (time.time() - request_start) * 1000
                            response_times.append(response_time)
                        else:
                            errors += 1
                except Exception as e:
                    errors += 1
                    print(f"Error in session creation test {i}: {e}")
            
            total_time = time.time() - start_time
            
            return {
                "endpoint": "session_creation",
                "iterations": iterations,
                "total_time": total_time,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "median_response_time": statistics.median(response_times) if response_times else 0,
                "requests_per_second": iterations / total_time,
                "errors": errors,
                "success_rate": ((iterations - errors) / iterations) * 100
            }
    
    async def test_event_ingestion(self, iterations: int = 100) -> Dict[str, Any]:
        """Test event ingestion endpoint performance."""
        print(f"🔍 Testing event ingestion ({iterations} requests)...")
        
        if not self.session_ids:
            print("⚠️  No sessions available for event ingestion test")
            return {}
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            response_times = []
            errors = 0
            
            for i in range(iterations):
                session_id = random.choice(self.session_ids)
                events = self._generate_mock_events(10)  # 10 events per request
                
                request_start = time.time()
                try:
                    async with session.post(
                        f"{self.api_base}/detection/sessions/{session_id}/events",
                        json=events
                    ) as response:
                        if response.status == 200:
                            response_time = (time.time() - request_start) * 1000
                            response_times.append(response_time)
                        else:
                            errors += 1
                except Exception as e:
                    errors += 1
                    print(f"Error in event ingestion test {i}: {e}")
            
            total_time = time.time() - start_time
            
            return {
                "endpoint": "event_ingestion",
                "iterations": iterations,
                "total_time": total_time,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "median_response_time": statistics.median(response_times) if response_times else 0,
                "requests_per_second": iterations / total_time,
                "errors": errors,
                "success_rate": ((iterations - errors) / iterations) * 100
            }
    
    async def test_session_analysis(self, iterations: int = 20) -> Dict[str, Any]:
        """Test session analysis endpoint performance."""
        print(f"🔍 Testing session analysis ({iterations} requests)...")
        
        if not self.session_ids:
            print("⚠️  No sessions available for analysis test")
            return {}
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            response_times = []
            errors = 0
            
            for i in range(iterations):
                session_id = random.choice(self.session_ids)
                
                request_start = time.time()
                try:
                    async with session.post(
                        f"{self.api_base}/detection/sessions/{session_id}/analyze"
                    ) as response:
                        if response.status == 200:
                            response_time = (time.time() - request_start) * 1000
                            response_times.append(response_time)
                        else:
                            errors += 1
                except Exception as e:
                    errors += 1
                    print(f"Error in session analysis test {i}: {e}")
            
            total_time = time.time() - start_time
            
            return {
                "endpoint": "session_analysis",
                "iterations": iterations,
                "total_time": total_time,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "median_response_time": statistics.median(response_times) if response_times else 0,
                "requests_per_second": iterations / total_time,
                "errors": errors,
                "success_rate": ((iterations - errors) / iterations) * 100
            }
    
    async def test_dashboard_endpoints(self, iterations: int = 50) -> Dict[str, Any]:
        """Test dashboard endpoints performance."""
        print(f"🔍 Testing dashboard endpoints ({iterations} requests)...")
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            response_times = []
            errors = 0
            
            for i in range(iterations):
                request_start = time.time()
                try:
                    async with session.get(f"{self.api_base}/dashboard/overview") as response:
                        if response.status == 200:
                            response_time = (time.time() - request_start) * 1000
                            response_times.append(response_time)
                        else:
                            errors += 1
                except Exception as e:
                    errors += 1
                    print(f"Error in dashboard test {i}: {e}")
            
            total_time = time.time() - start_time
            
            return {
                "endpoint": "dashboard_overview",
                "iterations": iterations,
                "total_time": total_time,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "median_response_time": statistics.median(response_times) if response_times else 0,
                "requests_per_second": iterations / total_time,
                "errors": errors,
                "success_rate": ((iterations - errors) / iterations) * 100
            }
    
    def _generate_mock_events(self, count: int) -> List[Dict[str, Any]]:
        """Generate mock events for testing."""
        event_types = ['keystroke', 'mouse_move', 'mouse_click', 'scroll', 'focus']
        events = []
        
        for i in range(count):
            event = {
                "event_type": random.choice(event_types),
                "timestamp": (datetime.now() + timedelta(seconds=i)).isoformat(),
                "element_id": f"element-{random.randint(1, 100)}",
                "element_type": random.choice(['input', 'button', 'div', 'span']),
                "page_url": "https://example.com/survey",
                "screen_width": 1920,
                "screen_height": 1080,
                "viewport_width": 1920,
                "viewport_height": 937
            }
            
            if event["event_type"] == "keystroke":
                event["key"] = random.choice("abcdefghijklmnopqrstuvwxyz")
            elif event["event_type"] in ["mouse_move", "mouse_click"]:
                event["x"] = random.randint(0, 1920)
                event["y"] = random.randint(0, 1080)
            
            events.append(event)
        
        return events
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive performance test suite."""
        print("🚀 Starting comprehensive API performance test...")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all tests
        tests = [
            await self.test_health_endpoint(100),
            await self.test_session_creation(50),
            await self.test_event_ingestion(100),
            await self.test_session_analysis(20),
            await self.test_dashboard_endpoints(50)
        ]
        
        total_time = time.time() - start_time
        
        # Compile results
        results = {
            "test_timestamp": datetime.now().isoformat(),
            "total_test_time": total_time,
            "tests": [test for test in tests if test],
            "summary": self._generate_summary(tests)
        }
        
        return results
    
    def _generate_summary(self, tests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics from test results."""
        if not tests:
            return {}
        
        all_response_times = []
        total_requests = 0
        total_errors = 0
        
        for test in tests:
            if test:
                all_response_times.extend([
                    test["avg_response_time"],
                    test["min_response_time"],
                    test["max_response_time"]
                ])
                total_requests += test["iterations"]
                total_errors += test["errors"]
        
        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "overall_success_rate": ((total_requests - total_errors) / total_requests) * 100 if total_requests > 0 else 0,
            "avg_response_time_across_endpoints": statistics.mean(all_response_times) if all_response_times else 0,
            "fastest_endpoint": min(tests, key=lambda x: x.get("avg_response_time", float('inf')))["endpoint"] if tests else None,
            "slowest_endpoint": max(tests, key=lambda x: x.get("avg_response_time", 0))["endpoint"] if tests else None
        }
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted test results."""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE TEST RESULTS")
        print("=" * 60)
        
        print(f"🕒 Test Timestamp: {results['test_timestamp']}")
        print(f"⏱️  Total Test Time: {results['total_test_time']:.2f} seconds")
        print()
        
        # Print individual test results
        for test in results['tests']:
            print(f"🔹 {test['endpoint'].upper()}")
            print(f"   Requests: {test['iterations']}")
            print(f"   Avg Response Time: {test['avg_response_time']:.2f}ms")
            print(f"   Min/Max Response Time: {test['min_response_time']:.2f}ms / {test['max_response_time']:.2f}ms")
            print(f"   Requests/Second: {test['requests_per_second']:.2f}")
            print(f"   Success Rate: {test['success_rate']:.1f}%")
            print(f"   Errors: {test['errors']}")
            print()
        
        # Print summary
        summary = results['summary']
        print("📈 SUMMARY")
        print("-" * 30)
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Total Errors: {summary['total_errors']}")
        print(f"Overall Success Rate: {summary['overall_success_rate']:.1f}%")
        print(f"Average Response Time: {summary['avg_response_time_across_endpoints']:.2f}ms")
        print(f"Fastest Endpoint: {summary['fastest_endpoint']}")
        print(f"Slowest Endpoint: {summary['slowest_endpoint']}")
        print()

async def main():
    """Main function to run performance tests."""
    parser = argparse.ArgumentParser(description='Bot Detection API Performance Tester')
    parser.add_argument('--url', default='http://localhost:8000', help='API base URL')
    parser.add_argument('--output', help='Output file for results (JSON)')
    parser.add_argument('--quick', action='store_true', help='Run quick test with fewer iterations')
    
    args = parser.parse_args()
    
    tester = APIPerformanceTester(args.url)
    
    try:
        results = await tester.run_comprehensive_test()
        tester.print_results(results)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"📄 Results saved to {args.output}")
            
    except Exception as e:
        print(f"❌ Error running performance tests: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 