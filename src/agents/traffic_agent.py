"""Traffic management chatbot agent."""

import pandas as pd
from langchain_core.messages import HumanMessage
from src.workflows.graph import create_workflow


class RoadNetworkChatBot:
    """Traffic management chatbot with human-in-the-loop workflow."""
    
    def __init__(self, verbose=True):
        self.app = create_workflow()
        self.verbose = verbose
    
    def query(self, question: str, run_name: str = None):
        """Process a traffic management query."""
        try:
            if self.verbose:
                print(f"Starting query: {question}")

            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=question)],
                "tool_calls": []
            }

            config = {
                "configurable": {"thread_id": "default"},
                "run_name": run_name or f"traffic_query_{len(question.split())}_words",
                "tags": ["traffic-management", "neo4j", "langgraph"],
                "metadata": {
                    "question_type": "traffic_incident" if "incident" in question.lower() else "general",
                    "question_length": len(question),
                    "timestamp": str(pd.Timestamp.now())
                }
            }

            # Run the graph
            result = self.app.invoke(initial_state, config=config)
            
            # Extract the final message from the result
            if result and "messages" in result and result["messages"]:
                final_message = result["messages"][-1]
                if hasattr(final_message, 'content'):
                    return final_message.content
                else:
                    return str(final_message)
            else:
                return "No response generated"
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Error occurred: {e}")
            return f"Error: {e}"
    
    def stream_query(self, question: str, run_name: str = None):
        """Stream the response for real-time updates."""
        initial_state = {
            "messages": [HumanMessage(content=question)],
            "tool_calls": []
        }

        config = {
            "configurable": {"thread_id": "stream"},
            "run_name": run_name or f"stream_traffic_query",
            "tags": ["traffic-management", "streaming", "neo4j"],
            "metadata": {"streaming": True}
        }
        
        for chunk in self.app.stream(initial_state, config=config):
            if self.verbose:
                print(f"📦 Chunk received: {list(chunk.keys())}")
            yield chunk
