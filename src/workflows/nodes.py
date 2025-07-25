"""Workflow node implementations."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_core.messages import HumanMessage
from src.core.state import GraphState
from config.llm import get_llm
from src.tools.neo4j_tools import get_schema, run_cypher_query
from src.tools.event_tools import extract_event_data, analyze_event_changes
from src.tools.plan_tools import generate_response_plan
from src.tools.storage_tools import store_event_details, store_event_plan
from prompts.system_prompts import system_prompt


def call_model(state: GraphState):
    """Call the LLM with the current state"""
    
    user_feedback = state.get("user_feedback", "")
    needs_revision = state.get("needs_revision", False)
    current_plan = state.get("current_plan", "")

    # Convert state messages to proper format
    system_message = {"role": "system", "content": system_prompt}

    valid_messages = []
    for msg in state["messages"]:
        if hasattr(msg, 'content') and msg.content and str(msg.content).strip():
            valid_messages.append(msg)
        elif hasattr(msg, 'tool_calls') and msg.tool_calls:
            # Keep messages with tool calls even if no content
            valid_messages.append(msg)
        else:
            print(f"⚠️ Skipping empty message: {type(msg)}")
    
    messages = [system_message] + valid_messages
    
    if needs_revision and user_feedback and user_feedback.lower() != "approve":
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
        
        print(f"🔄 Adding human feedback to LLM: {user_feedback}")

    # Get all tools
    tools = [get_schema, run_cypher_query, generate_response_plan, analyze_event_changes, extract_event_data, store_event_details, store_event_plan]
    
    # Bind tools to the LLM
    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)
    
    # Pass messages directly without conversion
    response = llm_with_tools.invoke(messages)
    
    return {
        "messages": [response],
        "needs_revision": False,  
        "user_feedback": ""       
    }


def human_feedback(state: GraphState):
    """Handle human feedback for response plan approval."""
    # Find the response plan from tool results
    plan = "No plan found"
    for message in reversed(state["messages"]):
        if hasattr(message, 'name') and message.name == "generate_response_plan":
            plan = message.content
            break
    
    print("=" * 60)
    print("🔍 HUMAN REVIEW REQUIRED")
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
            "current_plan": plan
        }
    else:
        return {
            "user_feedback": feedback,
            "final_approved": False,
            "needs_revision": True,  
            "revision_count": state.get("revision_count", 0) + 1,
            "current_plan": plan
        }
