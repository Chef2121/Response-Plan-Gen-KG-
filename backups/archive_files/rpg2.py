import os
from dotenv import load_dotenv
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
from prompts import *
load_dotenv()
langsmith_client = Client()

try:
    driver = GraphDatabase.driver(
        os.environ.get("NEO4J_URI"),
        auth=(os.environ.get("NEO4J_USERNAME"), os.environ.get("NEO4J_PASSWORD"))
    )

    driver.verify_connectivity()
    print("Neo4j connection successful")
    
    graph = Neo4jGraph(
        url=os.environ.get("NEO4J_URI"),
        username=os.environ.get("NEO4J_USERNAME"),
        password=os.environ.get("NEO4J_PASSWORD"),
        timeout=30  
    )
    

    llm = ChatAnthropic(
        model="claude-3-5-haiku-latest",
        temperature=0.3,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        max_tokens=4000
    )
    
    print("LLM initialized successfully")

except Exception as e:
    print(f"Setup failed: {e}")
    raise

@tool
def run_cypher_query(query: str) -> str:
    """Execute a Cypher query against the Neo4j database to retrieve road network data.
    
    Use this tool when you need to:
    - Find specific roads, intersections, or traffic data
    - Query relationships between road segments
    - Get traffic incident information
    - Analyze road network connectivity
    - Search for alternative routes
    
    Args:
        query: A valid Cypher query string
        
    Returns:
        Query results as a string (limited to 50 records)
    """
    try:
        with driver.session() as session:
            result = session.run(query)
            records = [dict(record) for record in result]
            return str(records[:50])
    except Exception as e:
        return f"Query error: {str(e)}"
    
@tool 
def get_schema() -> str:
    """
    Get the Neo4j database schema including all node labels, relationship types and properties
    Use this tool FIRST before running any Cypher queries to understand:
    - What node labels exist (e.g., Road, Intersection, TrafficIncident)
    - What relationship types are available (e.g., CONNECTS_TO, HAS_INCIDENT)
    - What properties each node/relationship has
    
    This ensures your Cypher queries use correct labels, properties, and relationships
    that actually exist in the database to avoid query errors.
    
    Returns:
        Complete database schema information
    """
    try:
        schema_info = graph.get_schema
        return str(schema_info)
    except Exception as e:
        return f"Schema error: {str(e)}"

@tool 
def generate_response_plan(context: str) -> str:
    """
    Generates a response plan based on the incident context retrieved from the knowledge graph
    Input: context (string) - Comprehensive context including incident details, VMS data importantly the id,
    event with their respective plan and plan command history to provide context.
    Returns: the explicit JSON formatted response plan with actions and VMS commands not the summary.
    """
    
    prompt = f"""
    You are an expert in traffic management specializing in creating response plans.
    Based on traffic incident information and psychological principles, generate a comprehensive response plan.
    
    Context: {context}
    
    {psychology_guidelines}
    
    RESPONSE PLAN FORMAT:
    Generate a response plan in the following JSON format:

    {{
        "plan_type": "Traffic Management Plan",
        "priority": "High/Medium/Low",
        "estimated_duration": "X minutes/hours",
        "traffic_management_actions": [
            {{
                "eqt_no": "VMS_EQUIPMENT_ID (from EQT_NO or EQT_EXT_ID)",
                "message_line_1": "Primary message (max 20 chars)",
                "message_line_2": "Secondary message (max 20 chars)",
                "display_duration": "X minutes",
                "distance": "distance from event in meters",
                "psychological_rationale": "Why this message is psychologically effective",
                "behavioral_goal": "Desired driver behavior",
                "urgency_level": "High/Medium/Low based on distance and severity",
                "reasoning": "Give your reasoning for all of the above, why this duration etc."
                "link_id": "The link id of where the VMS is located"
            }},

            {{
                "action": "Specific action to take",
                "location": "Where to implement",
                "resources_needed": "What resources are required",
                "timing": "When to implement"
            }}
        ],
        "messaging_strategy": {{
            "primary_emotion": "Urgency/Caution/Information",
            "cognitive_approach": "Simple/Clear/Direct",
            "behavioral_target": "Slow down/Merge/Avoid area"
        }},
        "emergency_response": {{
            "agencies_to_notify": [
                {{
                    "agency": "Police/Fire Services/Emergency Medical Services/Road Maintenance/Traffic Control",
                    "priority": "Immediate/High/Medium/Low",
                    "reason": "Specific reason for notification",
                    "contact_method": "Emergency dispatch/Direct call/Radio",
                    "resources_requested": "Number of units/personnel needed"
                }}
            ],
            "coordination_requirements": "How agencies should coordinate",
            "scene_management": "Who takes lead and scene control responsibilities"
        }},
        "justification": "Psychology-based explanation of messaging choices"
    }}

    RECOMMENDED ACTIONS GUIDELINES:
    1. Generate additional actions that could aid in controlling the event
    2. Provide a priority level to recommended event
    3. Give clear reasoning and thought behind each event
    4. State the required equipment and personnel to carry out said action
    5. Recommend at least 2 actions

    EMERGENCY RESPONSE AGENCY GUIDELINES:
    1. POLICE: Required for all accidents with injuries, traffic control, investigation
    2. FIRE SERVICES: Required for vehicle fires, fuel spills, extraction operations
    3. EMERGENCY MEDICAL SERVICES: Required for any injuries, medical emergencies
    4. ROAD MAINTENANCE: Required for debris cleanup, road surface damage, barrier repairs
    5. TRAFFIC CONTROL: Required for major incidents affecting multiple lanes or extended duration
    6. TOWING SERVICES: Required for vehicle removal, clearance operations
    
    PRIORITY LEVELS:
    - Immediate: Life-threatening situations, major blockages during rush hour
    - High: Injuries present, significant traffic impact, hazardous conditions
    - Medium: Property damage only, minor traffic disruption, routine cleanup
    - Low: Minor incidents, off-peak hours, minimal impact
    
    VMS MESSAGE RULES:
    0. CRITICAL: Use the exact distance_meters value from the VMS search results for each VMS
    1. Distance field must contain the actual calculated distance from VMS to incident location
    2. Use psychology guidelines above to craft messages
    3. Consider time of day (0800 = rush hour psychology)
    4. Match message urgency to distance from incident
    5. Use action-oriented language that triggers immediate response
    6. Avoid cognitive overload - keep messages simple and clear
    7. Consider emotional state of stressed commuters

    DISTANCE CALCULATION REQUIREMENTS:
    - For VMS on incident link: distance = 0 meters
    - For upstream VMS: use the distance_meters value from Cypher query results
    - Include exact distance in the "distance" field of each VMS action
    - Distance determines message urgency and content

    Generate practical VMS messages that will effectively influence driver behavior.
    """
    try: 
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error generating psychology-based response plan: {str(e)}"
# Update the tools list to include the new function
tools = [get_schema, run_cypher_query, generate_response_plan]
tool_node = ToolNode(tools)

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

class GraphState(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage], operator.add]
    tool_calls: List[dict]
    user_feedback: str
    final_approved: bool
    revision_count: int
    needs_revision: bool
    current_plan: str

def should_continue(state: GraphState):
    """Decide whether to continue with tools or end."""
    last_message = state["messages"][-1]
    needs_revison = state.get("needs_revision", False)

    if needs_revison:
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"  
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools" 
    
    # Second check: If we just got results from generate_response_plan tool
    if hasattr(last_message, 'name') and last_message.name == "generate_response_plan":
        print("🔍 Response plan generated - routing to human review")
        return "human_feedback"
    
    # Third check: Look for response plan in recent tool results
    for message in reversed(state["messages"][-3:]):  # Check last 3 messages
        if (hasattr(message, 'name') and 
            message.name == "generate_response_plan" and
            hasattr(message, 'content')):
            print("🔍 Found response plan in recent messages - routing to human review")
            return "human_feedback"
    
    # Fourth check: If AI message contains a response plan (backup)
    if (hasattr(last_message, 'content') and 
        last_message.content and
        ("plan_type" in last_message.content or "traffic_management_actions" in last_message.content)):
        print("🔍 AI message contains response plan - routing to human review")
        return "human_feedback"
    
    return END
    

# Then update your workflow routing:
def route_after_human_feedback(state: GraphState):
    """Route after human feedback - handle approve/reject properly."""
    final_approved = state.get("final_approved", False)
    user_feedback = state.get("user_feedback", "")
    
    print(f"🔄 Routing decision: approved={final_approved}, feedback='{user_feedback}'")
    
    if final_approved:
        print("✅ Plan approved - ending workflow")
        return END  
    else:
        print("Feedback recieved - rerunning with improvements") 
        return "agent" 


def call_model(state: GraphState):
    """Call the LLM with the current state."""
    
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

    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # Pass messages directly without conversion
    response = llm_with_tools.invoke(messages)
    
    return {
        "messages": [response],
        "needs_revision": False,  # Clear the flag
        "user_feedback": ""       # Clear processed feedback
    }

def human_feedback(state: GraphState):
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
    
    # Check if we already have feedback from a previous interrupt
    if state.get("user_feedback") and state.get("user_feedback") != "":
        feedback = state["user_feedback"]
        print(f"Using provided feedback: {feedback}")
        
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
                "needs_revision": True,  # Flag that we need revision
                "revision_count": state.get("revision_count", 0) + 1,
                "current_plan": plan
            }
    else:
        # For web UI: just store the plan and return to be interrupted
        # For console mode: ask for input (but this path won't be taken in web UI)
        print("Waiting for human feedback...")
        return {
            "user_feedback": "",
            "final_approved": False,
            "needs_revision": False,
            "current_plan": plan
        }


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
memory = MemorySaver()
# Compile the graph with interrupt capability - interrupt AFTER human_feedback extracts the plan
app = workflow.compile(checkpointer=memory, interrupt_after=["human_feedback"])

class RoadNetworkChatBot:
    def __init__(self, verbose = True):
        self.app = app
        self.verbose = verbose
    
    def query(self, question: str, run_name: str = None):
        try:
            if self.verbose:
                print(f"Starting query: {question}")

            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=question)],
                "tool_calls": []
            }

            config = {
                "configurable": {"thread_id": "default"},  # Add this line
                "run_name": run_name or f"traffic_query_{len(question.split())}_words",
                "tags": ["traffic-management", "neo4j", "langgraph"],
                "metadata": {
                    "question_type": "traffic_incident" if "incident" in question.lower() else "general",
                    "question_length": len(question),
                    "timestamp": str(pd.Timestamp.now())
                }
            }

            # Run the graph
            result = self.app.invoke(initial_state, config = config)
            
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
            "configurable": {"thread_id": "stream"},  # Add this line
            "run_name": run_name or f"stream_traffic_query",
            "tags": ["traffic-management", "streaming", "neo4j"],
            "metadata": {"streaming": True}
        }
        
        for chunk in self.app.stream(initial_state, config = config):
            if self.verbose:
                print(f"📦 Chunk received: {list(chunk.keys())}")
            yield chunk
    
    def query_with_interrupt(self, question: str, thread_id: str = None):
        """Query with interrupt capability for web UI."""
        initial_state = {
            "messages": [HumanMessage(content=question)],
            "tool_calls": [],
            "user_feedback": "",
            "final_approved": False,
            "revision_count": 0,
            "needs_revision": False,
            "current_plan": ""
        }

        config = {
            "configurable": {"thread_id": thread_id or "web_session"},
            "run_name": f"web_query_{thread_id}",
            "tags": ["traffic-management", "web-ui", "interrupt"],
            "metadata": {"web_mode": True}
        }
        
        # Run until interrupt (after human_feedback extracts the plan)
        result = self.app.invoke(initial_state, config)
        
        # The response plan should now be in the result's current_plan field
        response_plan = result.get("current_plan", "No plan found")
        
        return result, config, response_plan
    
    def continue_after_interrupt(self, feedback_text: str, approved: bool, config: dict):
        """Continue execution after human feedback."""
        # Update the state with human feedback
        update_state = {
            "user_feedback": feedback_text if not approved else "approve",
            "final_approved": approved,
            "needs_revision": not approved
        }
        
        # Continue from the interrupt
        result = self.app.invoke(update_state, config)
        return result

chatbot = RoadNetworkChatBot()
