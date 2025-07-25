"""Workflow routing logic."""

from langgraph.graph import END
from src.core.state import GraphState


def should_continue(state: GraphState):
    """Decide whether to continue with tools or end."""
    last_message = state["messages"][-1]
    needs_revision = state.get("needs_revision", False)

    if needs_revision:
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"  
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
     
    event_analysis_completed = False
    update_required = None
    
    for message in reversed(state["messages"][-10:]):  # Check last 10 messages
        if (hasattr(message, 'name') and 
            message.name == "analyze_event_changes" and
            hasattr(message, 'content')):
            event_analysis_completed = True
            # Try to extract update_required from the analysis result
            try:
                import json
                analysis_result = json.loads(message.content)
                update_required = analysis_result.get("update_required", True)
            except:
                # If we can't parse, default to requiring update for safety
                update_required = True
            break
    
    # If analysis not completed yet, continue (agent should run analyze_event_changes)
    if not event_analysis_completed:
        return END  # Let the agent continue its workflow
    
    # If analysis says no update required, end the workflow
    if update_required == False:
        print("✅ Event analysis complete: No response plan update required")
        return END
    
    # If update is required, check for response plan generation
    for message in reversed(state["messages"][-5:]):
        if (hasattr(message, 'name') and 
            message.name == "generate_response_plan" and
            hasattr(message, 'content')):
            print("🔍 Response plan generated - routing to human review")
            return "human_feedback"
    
    # Check if AI message contains a response plan (backup detection)
    if (hasattr(last_message, 'content') and 
        last_message.content and
        ("plan_type" in last_message.content or "traffic_management_actions" in last_message.content)):
        print("🔍 AI message contains response plan - routing to human review")
        return "human_feedback"
    
    return END


def route_after_human_feedback(state: GraphState):
    """Route after human feedback"""
    final_approved = state.get("final_approved", False)
    user_feedback = state.get("user_feedback", "")
    
    print(f"🔄 Routing decision: approved={final_approved}, feedback='{user_feedback}'")
    
    if final_approved:
        print("✅ Plan approved - ending workflow")
        return END  
    else:
        print("Feedback received - rerunning with improvements") 
        return "agent"
