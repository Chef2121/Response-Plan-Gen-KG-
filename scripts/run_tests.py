"""Test runner with performance tracking."""

import sys
import os
import time
import json
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.traffic_agent import RoadNetworkChatBot

class PerformanceTracker:
    """Track and analyze test performance."""
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
    
    def run_test(self, name: str, query: str, expected_outcome: str = None) -> Dict[str, Any]:
        """Run a single test and track performance."""
        print(f"\n🧪 Running test: {name}")
        print(f"Query: {query[:100]}...")
        
        start_time = time.time()
        
        try:
            chatbot = RoadNetworkChatBot(verbose=False)
            result = chatbot.query(query, run_name=f"test_{name}")
            
            end_time = time.time()
            duration = end_time - start_time
            
            success = "Error:" not in result
            
            test_result = {
                "name": name,
                "query": query,
                "result": result,
                "duration": duration,
                "expected": expected_outcome,
                "success": success,
                "timestamp": time.time(),
                "error": None if success else result
            }
            
            self.test_results.append(test_result)
            
            print(f"✅ Success: {success}")
            print(f"⏱️ Duration: {duration:.2f}s")
            if not success:
                print(f"❌ Error: {result}")
            
            return test_result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            test_result = {
                "name": name,
                "query": query,
                "result": None,
                "duration": duration,
                "expected": expected_outcome,
                "success": False,
                "timestamp": time.time(),
                "error": str(e)
            }
            
            self.test_results.append(test_result)
            print(f"❌ Test failed: {e}")
            
            return test_result
    
    def run_test_suite(self):
        """Run the complete test suite."""
        
        test_cases = [
            {
                "name": "basic_incident",
                "query": "A car accident has occurred at link_id 17840006094278, the time is 0800, the event severity is medium, the event type is accident",
                "expected": "Response plan generated"
            },
            {
                "name": "high_severity_incident", 
                "query": "Event id (12345): At 08:45, a major multi-vehicle accident occurred on road link 17840006094278. Three lanes are blocked, causing a queue of 1500 meters. High severity.",
                "expected": "High priority response plan"
            },
            {
                "name": "breakdown_incident",
                "query": "Vehicle breakdown on link 17840006094277 at 1430. Right lane blocked, queue length 400 meters. Medium severity.",
                "expected": "Medium priority response plan"
            },
            {
                "name": "weather_incident",
                "query": "Weather-related incident on link 17840006094278. Heavy fog causing visibility issues. Low severity but high traffic volume.",
                "expected": "Weather-appropriate messaging"
            }
        ]
        
        print("🚀 Starting test suite...")
        print("=" * 60)
        
        for test_case in test_cases:
            self.run_test(
                name=test_case["name"],
                query=test_case["query"],
                expected_outcome=test_case["expected"]
            )
        
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """Print test summary."""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for test in self.test_results if test["success"])
        failed_tests = total_tests - successful_tests
        
        if total_tests > 0:
            avg_duration = sum(test["duration"] for test in self.test_results) / total_tests
        else:
            avg_duration = 0
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏱️ Average Duration: {avg_duration:.2f}s")
        print(f"📈 Success Rate: {(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"  - {test['name']}: {test['error']}")
    
    def save_results(self):
        """Save test results to file."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            print(f"\n💾 Results saved to: {filename}")
        except Exception as e:
            print(f"⚠️ Failed to save results: {e}")

def main():
    """Main test runner."""
    tracker = PerformanceTracker()
    
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        test_query = sys.argv[2] if len(sys.argv) > 2 else "Test query"
        tracker.run_test(test_name, test_query)
    else:
        # Run full suite
        tracker.run_test_suite()

if __name__ == "__main__":
    main()
