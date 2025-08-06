"""Workflow graph implementation for traffic management."""

from typing import TypedDict, List, Annotated
import operator
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic
import os
import pandas as pd

from src.tools.workflow_tools import tools, setup_connections
from prompts.system_prompts import system_prompt


class GraphState(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage], operator.add]
    tool_calls: List[dict]
    user_feedback: str
    final_approved: bool
    revision_count: int
    needs_revision: bool
    current_plan: str
    event_history: List[dict]
    event_id: str
    previous_event_state: str
    current_event_state: str
    event_analysis_completed: bool
    update_required: bool
    approved_plan: bool
    response_plan_generated: bool
    event_stored: bool
    plan_stored: bool


def should_continue(state: GraphState):
    """Decide whether to continue with tools or end."""
    last_message = state["messages"][-1]
    needs_revision = state.get("needs_revision", False)
    final_approved = state.get("final_approved", False)
    event_stored = state.get("event_stored", False)
    plan_stored = state.get("plan_stored", False)
    event_analysis_completed = state.get("event_analysis_completed", False)
    update_required = state.get("update_required", None)

    # Check if storage operations are complete (only after human approval)
    for message in reversed(state["messages"][-20:]):  
        if hasattr(message, 'name') and message.name == "store_event_details":
            if hasattr(message, 'content') and "successfully" in message.content.lower():
                event_stored = True
                print("Event storage detected")
                break
    
    for message in reversed(state["messages"][-20:]):  
        if hasattr(message, 'name') and message.name == "store_event_plan":
            if hasattr(message, 'content') and "successfully" in message.content.lower():
                plan_stored = True
                print("Plan storage detected")
                break
    
    print(f"Storage status: event_stored={event_stored}, plan_stored={plan_stored}, final_approved={final_approved}")

    # If storage is complete, end the workflow
    if plan_stored and event_stored and final_approved:
        print("Storage completed successfully - ending workflow")
        return END
    
    # Check for event analysis completion and update_required
    for message in reversed(state["messages"][-15:]): 
        if (hasattr(message, 'name') and 
            message.name == "analyze_event_changes" and
            hasattr(message, 'content')):
            event_analysis_completed = True
            try:
                import json
                analysis_result = json.loads(message.content)
                update_required = analysis_result.get("update_required", True)
                print(f"Analysis result: update_required={update_required}")
            except Exception as e:
                print(f"Failed to parse analysis result: {e}")
                update_required = True
            break
    # If analysis not completed yet, continue with tools
    if not event_analysis_completed:
        print("Event not analyzed, continuing with tools")
        return "tools" 
    
    # If analysis says no update required, end the workflow
    if update_required == False:
        print("Event analysis complete: No response plan update required - ending workflow")
        return END
    
    # Handle revision cases
    if needs_revision:
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"  
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    if final_approved:
        print("Plan approved - continuing to storage")
        return "tools"
    
    # Check if response plan was generated 
    response_plan_generated = False
    for message in reversed(state["messages"][-10:]):
        if (hasattr(message, 'name') and 
            message.name == "generate_response_plan" and
            hasattr(message, 'content')):
            response_plan_generated = True
            print("Response plan generated - routing to human review")
            return "human_feedback"
    
    # Backup detection for response plan in AI message
    if (hasattr(last_message, 'content') and 
        last_message.content and
        ("plan_type" in last_message.content or "traffic_management_actions" in last_message.content)):
        print("AI message contains response plan - routing to human review")
        return "human_feedback"
    
    # If update required but no response plan generated yet, continue with tools
    if update_required == True and not response_plan_generated:
        print("Response plan not generated, continue workflow")
        return "tools"
    
    print("Default case - continuing with tools")
    return "tools"


def route_after_human_feedback(state: GraphState):
    """Route after human feedback"""
    final_approved = state.get("final_approved", False)
    user_feedback = state.get("user_feedback", "")
    
    print(f"Routing decision: approved={final_approved}, feedback='{user_feedback}'")
    
    if final_approved:
        print("Plan approved - routing back to agent to store in database")
        return "agent"  
    else:
        print("Feedback received - rerunning with improvements") 
        return "agent" 


def call_model(state: GraphState):
    """Call the LLM with the current state"""
    
    user_feedback = state.get("user_feedback", "")
    needs_revision = state.get("needs_revision", False)
    current_plan = state.get("current_plan", "")
    final_approved = state.get("final_approved", False)

    # Initialize LLM
    llm = ChatAnthropic(
        model="claude-3-5-haiku-latest",
        temperature=0.3,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=4000
    )

    system_message = {"role": "system", "content": system_prompt}

    valid_messages = []
    for msg in state["messages"]:
        if hasattr(msg, 'content') and msg.content and str(msg.content).strip():
            valid_messages.append(msg)
        elif hasattr(msg, 'tool_calls') and msg.tool_calls:
            valid_messages.append(msg)
        else:
            print(f"Skipping empty message: {type(msg)}")
    
    messages = [system_message] + valid_messages
    
    # If plan was approved, instruct to store it
    if final_approved and current_plan:
        event_stored = False
        plan_stored = False
        
        for message in reversed(state["messages"][-30:]):
            if (hasattr(message, 'name') and message.name == "store_event_details" and 
                hasattr(message, 'content') and "successfully" in message.content.lower()):
                event_stored = True
            if (hasattr(message, 'name') and message.name == "store_event_plan" and
                hasattr(message, 'content') and "successfully" in message.content.lower()):
                plan_stored = True
        
        if not event_stored and not plan_stored:
            storage_prompt = """
            The response plan has been approved. Store the event details first using store_event_details tool.
            Extract the event_id and event data from previous messages.
            """
        elif event_stored and not plan_stored:
            storage_prompt = f"""
            Event details have been stored successfully. Now store the approved response plan using store_event_plan tool.
            
            APPROVED PLAN TO STORE:
            {current_plan}
            """
        else:
            # Both are done, shouldn't reach here
            storage_prompt = "Both event and plan have been stored successfully."
        
        storage_message = HumanMessage(content=storage_prompt)
        messages.append(storage_message)
        
        print(f"Storage instruction: event_stored={event_stored}, plan_stored={plan_stored}")
    
    elif needs_revision and user_feedback and user_feedback.lower() != "approve":
        revision_prompt = f"""
        HUMAN REVIEWER FEEDBACK: {user_feedback}
        CURRENT PLAN: {current_plan}
        
        The human reviewer has provided feedback on your response plan. 
        Please revise the plan based on this feedback while maintaining:
        1. All safety protocols
        2. Psychological messaging principles  
        3. Proper JSON format
        4. VMS equipment IDs from the database
        
        You can also use tools to search for more VMS if required
        Generate an improved response plan that addresses the reviewer's concerns.
        """
        
        feedback_message = HumanMessage(content=revision_prompt)
        messages.append(feedback_message)
        
        print(f"Adding human feedback to LLM: {user_feedback}")

    llm_with_tools = llm.bind_tools(tools)
    
    response = llm_with_tools.invoke(messages)
    
    return {
        "messages": [response],
        "needs_revision": False,  
        "user_feedback": "",
        "final_approved": final_approved,  
        "current_plan": current_plan 
    }

def human_feedback(state: GraphState):
    plan = "No plan found"
    for message in reversed(state["messages"]):
        if hasattr(message, 'name') and message.name == "generate_response_plan":
            plan = message.content
            break
    
    print("=" * 60)
    print("HUMAN REVIEW REQUIRED")
    print("=" * 60)
    print("Response Plan:")
    print(plan)
    print("=" * 60)
    print("Type 'approve' to accept or anything else to reject:")
    
    feedback = input("Your decision: ")

    if feedback.strip().lower() == "approve":
        return {
            "user_feedback": feedback,
            "final_approved": True,
            "needs_revision": False,
            "current_plan": plan,
            "event_analysis_completed": state.get("event_analysis_completed", True),  
            "update_required": state.get("update_required", True)  
        }
    else:
        return {
            "user_feedback": feedback,
            "final_approved": False,
            "needs_revision": True,  
            "revision_count": state.get("revision_count", 0) + 1,
            "current_plan": plan,
            "event_analysis_completed": state.get("event_analysis_completed", True), 
            "update_required": state.get("update_required", True)  
        }


def custom_parsing_error_handler(error):
    """Custom handler to see what the LLM actually outputs"""
    print("=" * 50)
    print("PARSING ERROR DETECTED!")
    print("Error message:", str(error))
    print("=" * 50)
    
    # Try to extract the actual LLM output from the error
    error_str = str(error)
    if "Could not parse LLM output:" in error_str:
        # Extract the actual output
        start_idx = error_str.find("Could not parse LLM output:") + len("Could not parse LLM output:")
        end_idx = error_str.find("For troubleshooting")
        if end_idx == -1:
            actual_output = error_str[start_idx:].strip()
        else:
            actual_output = error_str[start_idx:end_idx].strip()
        
        print("ACTUAL LLM OUTPUT:")
        print(actual_output)
        print("=" * 50)
        
        # Return a formatted response
        return f"LLM tried to use tool but format was wrong. Raw output: {actual_output}"
    
    return f"Parsing error: {error}"


def create_workflow():
    """Create the workflow graph."""
    
    # Setup connections
    setup_connections()
    
    # Create tool node
    tool_node = ToolNode(tools)
    
    # Create workflow
    workflow = StateGraph(GraphState)

    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.add_node("human_feedback", human_feedback)
    workflow.set_entry_point("agent")

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

    workflow.add_edge("tools", "agent")
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app
