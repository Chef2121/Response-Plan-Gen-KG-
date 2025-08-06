"""
Main entry point for the traffic management system.
This script demonstrates the complete workflow from your notebook.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    """Main demonstration function that replicates your notebook workflow."""
    
    print("🚦 TRAFFIC MANAGEMENT SYSTEM")
    print("=" * 50)
    
    try:
        # Test imports first
        from langchain_anthropic import ChatAnthropic
        from langchain_neo4j import Neo4jGraph
        from neo4j import GraphDatabase
        from langgraph.graph import StateGraph, END
        from langgraph.prebuilt import ToolNode
        from langchain_core.tools import tool
        from langchain_core.messages import HumanMessage, AIMessage
        from typing import TypedDict, List, Annotated
        import operator
        import pandas as pd
        from langsmith import Client
        from langgraph.checkpoint.memory import MemorySaver
        from prompts import psychology_guidelines, schema_docs, system_prompt, neo4j_cs
        import json
        from datetime import datetime
        
        print("✅ All imports successful")
        
        # Initialize components
        print("\n🔧 Setting up connections...")
        from src.agents.traffic_agent import RoadNetworkChatBot
        
        # Initialize chatbot (equivalent to your notebook cell)
        print("\n🤖 Initializing chatbot...")
        chatbot = RoadNetworkChatBot(verbose=True)
        print("✅ Chatbot initialized successfully")
        
        # Test query (equivalent to your notebook test)
        print("\n🚗 Testing with incident query...")
        incident_query = "the event_id is 38382929, At 12:45 this morning, a multi-vehicle accident occurred on road link 17840006094278 near the junction with Elmwood Avenue Motorway. Two lanes are currently blocked, causing a queue of approximately 3000 meters. Emergency services are on site, and the incident has been active for 35 minutes. The severity is high due to the number of vehicles involved and the impact on traffic flow. Additional hazards include spilled fuel and debris on the road. Weather conditions are foggy, contributing to low visibility. Traffic volume is high due to rush hour."
        
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
        print("  2. Set up your environment variables in .env file")
        print("  3. Run the setup script: python scripts/setup_system.py")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Try running the setup script first: python scripts/setup_system.py")
        return False

def demo_workflow_visualization():
    """Demonstrate workflow visualization like in the notebook."""
    
    print("\n🎨 WORKFLOW VISUALIZATION DEMO")
    print("=" * 50)
    
    try:
        from scripts.visualize_workflow import visualize_workflow
        return visualize_workflow()
    except Exception as e:
        print(f"❌ Visualization error: {e}")
        return False

def interactive_demo():
    """Interactive demo mode."""
    
    print("\n🎮 INTERACTIVE DEMO MODE")
    print("=" * 50)
    
    try:
        from src.agents.traffic_agent import RoadNetworkChatBot
        
        chatbot = RoadNetworkChatBot(verbose=True)
        
        print("✅ Chatbot ready!")
        print("💡 Enter your traffic incident queries, or 'quit' to exit")
        print("📝 Example: 'A car accident occurred on link 17840006094278 at 0800 with high severity'")
        
        while True:
            print("\n" + "-"*50)
            query = input("🚗 Enter incident query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not query:
                print("❌ Please enter a valid query")
                continue
            
            print(f"\n🔄 Processing: {query[:50]}...")
            print("="*50)
            
            try:
                result = chatbot.query(query)
                print(f"\n📋 Result:\n{result}")
            except Exception as e:
                print(f"❌ Error processing query: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Interactive demo error: {e}")
        return False
        
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
    
    import sys
    
    # Check command line arguments for different demo modes
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "setup":
            print("\n🔧 Running setup...")
            from scripts.setup_system import setup_connections, check_environment
            if check_environment():
                setup_connections()
        
        elif mode == "test":
            print("\n🧪 Running tests...")
            from scripts.test_system import run_all_tests
            run_all_tests()
            
        elif mode == "visualize":
            print("\n🎨 Generating workflow visualization...")
            demo_workflow_visualization()
            
        elif mode == "interactive":
            print("\n🎮 Starting interactive mode...")
            interactive_demo()
            
        else:
            print(f"❌ Unknown mode: {mode}")
            print("💡 Available modes: setup, test, visualize, interactive")
            
    else:
        # Default: run the main demo
        success = main()
        
        if success:
            print("\n🎉 Demo completed successfully!")
            print("💡 Try other modes:")
            print("  python main.py setup      - Setup connections")
            print("  python main.py test       - Run tests") 
            print("  python main.py visualize  - Generate workflow diagram")
            print("  python main.py interactive - Interactive mode")
        else:
            print("\n❌ Demo failed!")
            print("💡 Try: python main.py setup")
