"""Main workflow graph construction."""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from src.core.state import GraphState
from src.workflows.nodes import call_model, human_feedback
from src.workflows.routing import should_continue, route_after_human_feedback
from src.tools.neo4j_tools import get_schema, run_cypher_query
from src.tools.event_tools import extract_event_data, analyze_event_changes
from src.tools.plan_tools import generate_response_plan
from src.tools.storage_tools import store_event_details, store_event_plan


def create_workflow():
    """Create and compile the traffic management workflow."""
    
    # Define tools
    tools = [
        get_schema, 
        run_cypher_query, 
        generate_response_plan, 
        analyze_event_changes, 
        extract_event_data, 
        store_event_details, 
        store_event_plan
    ]
    tool_node = ToolNode(tools)

    # Build the graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.add_node("human_feedback", human_feedback)
    
    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "human_feedback": "human_feedback",
            END: END
        }
    )

    workflow.add_conditional_edges(
        "human_feedback",
        route_after_human_feedback,
        {
            "agent": "agent",  
            END: END         
        }
    )

    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")
    
    # Add memory
    memory = MemorySaver()
    
    # Compile the graph
    app = workflow.compile(checkpointer=memory)
    
    return app
