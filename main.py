"""
Main entry point for the traffic management system.
This script demonstrates the complete workflow from your notebook.
"""

import sys
import os

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """Main demonstration function that replicates your notebook workflow."""
    
    print("🚦 TRAFFIC MANAGEMENT SYSTEM")
    print("=" * 50)
    
    try:
        # Import after adding to path
        from src.agents.traffic_agent import RoadNetworkChatBot
        
        print("✅ Successfully imported traffic agent")
        
        # Initialize chatbot (equivalent to your notebook cell)
        print("\n🤖 Initializing chatbot...")
        chatbot = RoadNetworkChatBot(verbose=True)
        print("✅ Chatbot initialized successfully")
        
        # Test query (equivalent to your notebook test)
        print("\n🚗 Testing with incident query...")
        incident_query = """Event id (38382929): At 08:45 this morning, a multi-vehicle accident occurred on road link 17840006094278 near the junction with Elmwood Avenue. Two lanes are currently blocked, causing a queue of approximately 750 meters. Emergency services are on site, and the incident has been active for 35 minutes. The severity is high due to the number of vehicles involved and the impact on traffic flow. Additional hazards include spilled fuel and debris on the road. Weather conditions are foggy, contributing to low visibility. Traffic volume is high due to rush hour."""
        
        print(f"Query: {incident_query[:100]}...")
        print("\n" + "="*50)
        print("🔄 Processing (this will include human review)...")
        print("="*50)
        
        result = chatbot.query(incident_query)
        
        print("\n📋 FINAL RESULT:")
        print("="*50)
        print(result)
        
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\n💡 Make sure you have:")
        print("  1. Installed all requirements: pip install -r requirements.txt")
        print("  2. Set up your .env file with credentials")
        print("  3. Neo4j database is running and accessible")
        return False
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Traffic Management System Demo...")
    print("This replicates the functionality from your rpgjv2human.ipynb notebook")
    print("")
    
    success = main()
    
    if success:
        print("\n🎉 Demo completed successfully!")
        print("\n📚 Next steps:")
        print("  - Check docs/api_reference.md for API documentation")
        print("  - Run scripts/demo.py for more examples")
        print("  - Use notebooks/development/workflow_testing.ipynb for development")
    else:
        print("\n❌ Demo failed. Please check the error messages above.")
        sys.exit(1)
