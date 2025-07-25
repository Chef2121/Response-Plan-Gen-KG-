"""Demonstration script for the traffic management system."""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.traffic_agent import RoadNetworkChatBot
from src.utils.formatters import format_json_response

def demo_basic_incident():
    """Demonstrate basic incident handling."""
    print("🚗 DEMO: Basic Traffic Incident")
    print("=" * 50)
    
    chatbot = RoadNetworkChatBot(verbose=True)
    
    incident_query = """
    Event id (DEMO001): A car accident has occurred on road link 17840006094278 at 08:45. 
    Two lanes are currently blocked, causing a queue of approximately 750 meters. 
    The incident has been active for 25 minutes. Severity is medium due to moderate traffic impact.
    Traffic volume is high due to rush hour.
    """
    
    print("Query:", incident_query)
    print("\n" + "="*50)
    
    result = chatbot.query(incident_query)
    
    print("Result:")
    print(result)
    return result

def demo_high_severity_incident():
    """Demonstrate high severity incident handling."""
    print("\n🚨 DEMO: High Severity Incident")
    print("=" * 50)
    
    chatbot = RoadNetworkChatBot(verbose=True)
    
    incident_query = """
    Event id (DEMO002): URGENT - Multi-vehicle accident on road link 17840006094278 at 07:30.
    Three lanes blocked out of four. Queue length exceeds 2000 meters and growing.
    Multiple injuries reported. Emergency services on scene. Fuel spill detected.
    Incident duration: 45 minutes. HIGH SEVERITY - Major traffic disruption.
    Rush hour traffic - maximum impact expected.
    """
    
    print("Query:", incident_query)
    print("\n" + "="*50)
    
    result = chatbot.query(incident_query)
    
    print("Result:")
    print(result)
    return result

def demo_streaming_workflow():
    """Demonstrate streaming workflow."""
    print("\n📡 DEMO: Streaming Workflow")
    print("=" * 50)
    
    chatbot = RoadNetworkChatBot(verbose=True)
    
    incident_query = "Vehicle breakdown on link 17840006094277. Right lane blocked, queue 400m."
    
    print("Query:", incident_query)
    print("\nStreaming response:")
    print("-" * 30)
    
    for chunk in chatbot.stream_query(incident_query):
        for node, output in chunk.items():
            print(f"📦 Node: {node}")
            if "messages" in output:
                for msg in output["messages"]:
                    if hasattr(msg, 'content') and msg.content:
                        print(f"💬 Content: {msg.content[:100]}...")

def interactive_demo():
    """Interactive demonstration mode."""
    print("\n🎮 INTERACTIVE DEMO MODE")
    print("=" * 50)
    print("Enter traffic incident descriptions, or 'quit' to exit.")
    print("Example: 'Accident on link 17840006094278, 2 lanes blocked, high severity'")
    
    chatbot = RoadNetworkChatBot(verbose=True)
    
    while True:
        print("\n" + "-" * 30)
        query = input("🚦 Enter incident description: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("👋 Demo ended. Goodbye!")
            break
        
        if not query:
            print("Please enter a valid incident description.")
            continue
        
        print("\n🔄 Processing...")
        try:
            result = chatbot.query(query)
            print("\n📋 Response:")
            print(result)
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main demo function."""
    print("🚦 TRAFFIC MANAGEMENT SYSTEM DEMO")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        demo_type = sys.argv[1].lower()
        
        if demo_type == "basic":
            demo_basic_incident()
        elif demo_type == "high":
            demo_high_severity_incident()
        elif demo_type == "stream":
            demo_streaming_workflow()
        elif demo_type == "interactive":
            interactive_demo()
        else:
            print(f"Unknown demo type: {demo_type}")
            print("Available demos: basic, high, stream, interactive")
    else:
        # Run all demos
        print("Running all demonstrations...\n")
        
        try:
            demo_basic_incident()
            demo_high_severity_incident()
            
            print("\n🎯 Demo completed successfully!")
            print("\nTo run specific demos:")
            print("  python scripts/demo.py basic      - Basic incident demo")
            print("  python scripts/demo.py high       - High severity demo") 
            print("  python scripts/demo.py stream     - Streaming workflow demo")
            print("  python scripts/demo.py interactive - Interactive mode")
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
