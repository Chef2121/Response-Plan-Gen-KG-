"""Comprehensive test script based on notebook implementation."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, current_dir)

def test_complete_workflow():
    """Test the complete workflow like in the notebook."""
    
    print("🧪 COMPREHENSIVE WORKFLOW TEST")
    print("=" * 60)
    
    try:
        # Import after adding to path
        from src.agents.traffic_agent import RoadNetworkChatBot
        
        print("✅ Successfully imported traffic agent")
        
        # Initialize chatbot (equivalent to notebook cell)
        print("\n🤖 Initializing chatbot...")
        chatbot = RoadNetworkChatBot(verbose=True)
        print("✅ Chatbot initialized successfully")
        
        # Test incident query (same as notebook)
        print("\n🚗 Testing with incident query...")
        incident_query = "the event_id is 38382929, At 12:45 this morning, a multi-vehicle accident occurred on road link 17840006094278 near the junction with Elmwood Avenue Motorway. Two lanes are currently blocked, causing a queue of approximately 3000 meters. Emergency services are on site, and the incident has been active for 35 minutes. The severity is high due to the number of vehicles involved and the impact on traffic flow. Additional hazards include spilled fuel and debris on the road. Weather conditions are foggy, contributing to low visibility. Traffic volume is high due to rush hour."
        
        print(f"Query: {incident_query[:100]}...")
        print("\n" + "="*60)
        print("🔄 Processing (this will include human review)...")
        print("="*60)
        
        # Run the query
        result = chatbot.query(incident_query)
        
        print("\n📋 FINAL RESULT:")
        print("="*60)
        print(result)
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\n💡 Make sure you have:")
        print("  1. Installed all requirements: pip install -r requirements.txt")
        print("  2. Set up your environment variables in .env file")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_streaming_workflow():
    """Test the streaming workflow like in the notebook."""
    
    print("\n🌊 STREAMING WORKFLOW TEST")
    print("=" * 60)
    
    try:
        from src.agents.traffic_agent import RoadNetworkChatBot
        
        chatbot = RoadNetworkChatBot(verbose=True)
        
        # Simple test query for streaming
        test_query = "A car accident has occurred at link_id 17840006094278, the time is 0800, the event severity is medium, the event type is accident"
        
        print(f"Streaming query: {test_query}")
        print("\n" + "="*60)
        print("🔄 Streaming chunks (this will include human review)...")
        print("="*60)
        
        # Stream the response
        for chunk in chatbot.stream_query(test_query):
            for node, output in chunk.items():
                print(f"\n📦 Node: {node}")
                if "messages" in output:
                    for msg in output["messages"]:
                        if hasattr(msg, 'content') and msg.content:
                            print(f"💬 Content: {msg.content[:200]}...")
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            print(f"🔧 Tool calls: {[tc.get('name', 'unknown') for tc in msg.tool_calls]}")
                
                # Show human feedback if present
                if "user_feedback" in output:
                    print(f"👤 Human Feedback: {output['user_feedback']}")
                if "final_approved" in output:
                    print(f"✅ Final Approval: {output['final_approved']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Streaming Error: {e}")
        return False

def run_all_tests():
    """Run all test scenarios."""
    
    print("🚀 RUNNING ALL TESTS")
    print("=" * 80)
    
    tests = [
        ("Complete Workflow", test_complete_workflow),
        ("Streaming Workflow", test_streaming_workflow)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        
        try:
            success = test_func()
            results[test_name] = "✅ PASSED" if success else "❌ FAILED"
        except Exception as e:
            results[test_name] = f"❌ ERROR: {e}"
    
    # Print summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    for test_name, result in results.items():
        print(f"{test_name}: {result}")
    
    # Overall result
    passed = sum(1 for r in results.values() if "PASSED" in r)
    total = len(results)
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests completed successfully!")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    # You can run individual tests or all tests
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "complete":
            test_complete_workflow()
        elif sys.argv[1] == "stream":
            test_streaming_workflow()
        elif sys.argv[1] == "all":
            run_all_tests()
        else:
            print("Usage: python test_system.py [complete|stream|all]")
    else:
        # Default: run complete workflow test
        test_complete_workflow()
