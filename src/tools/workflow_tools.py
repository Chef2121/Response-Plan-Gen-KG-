"""Tools for the traffic management system based on the notebook implementation."""

import os
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_neo4j import Neo4jGraph
from neo4j import GraphDatabase
from datetime import datetime

# Initialize global variables (should be initialized in setup)
driver = None
graph = None
llm = None
CACHED_SCHEMA = None

def setup_connections():
    """Setup database and LLM connections."""
    global driver, graph, llm, CACHED_SCHEMA
    
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
        try:
            CACHED_SCHEMA = graph.get_schema
            print("Schema cached successfully")
            print(f"Schema preview: {str(CACHED_SCHEMA)[:200]}...")
        except Exception as schema_error:
            print(f"Could not cache schema: {schema_error}")
            CACHED_SCHEMA = None

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
    - search for past event details either by the link id or the event id
    - Query relationships between road segments
    - Get traffic incident information
    - Analyze road network connectivity
    - Search for alternative route
    - Searching for VMS (FOR THE DISTANCE PLEASE GET FROM vms_range_get output)
    
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

    print("Retrieving Schema from NEO4J...")
    try:
        # Use cached schema if available
        if CACHED_SCHEMA is not None:
            return str(CACHED_SCHEMA)
        else:
            # Fallback to direct query if cache failed
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
    
    print("Generating Response plan...")

    # Import psychology guidelines from the prompts module
    from prompts.psychology_guidelines import psychology_guidelines

    prompt = f"""
    You are an expert in traffic management specializing in creating response plans.
    Based on traffic incident information and psychological principles, generate a comprehensive response plan.
    
    Context: {context}
    USE ALL the VMS provided to ensure sufficient coverage
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
    
    PSYCHOLOGICAL MESSAGING RULES:
    1. Use psychology guidelines above to craft messages
    2. Consider time of day (0800 = rush hour psychology)
    3. Match message urgency to distance from incident
    4. Use action-oriented language that triggers immediate response
    5. Avoid cognitive overload - keep messages simple and clear
    6. Consider emotional state of stressed commuters

    Generate practical VMS messages that will effectively influence driver behavior and prevent secondary accidents.
    """
    
    try:
        response = llm.invoke(prompt)
        print("Response plan generated. Awaiting Human Feedback")
        return response.content
    except Exception as e:
        return f"Error generating psychology-based response plan: {str(e)}"
    
@tool
def extract_event_data(event_description: str) -> str:
    """
    Extract structured event data from user input or event updates.
    
    Args:
        event_description: Description of the traffic event or incident
    
    Returns:
        JSON with structured event data for comparison
    """
    print("Extracting event data from query.")
    prompt = f"""
    Extract structured data from this traffic event description:
    CHECK THE ROAD TYPE AS THIS WILL HAVE SIGNIFICANT IMPACT ON THE PLAN
    MUST TAKE INTO CONSIDERATION OF THE ROAD TYPE
    EVENT DESCRIPTION: {event_description}
    
    Return the data in this JSON format:
    {{
        "event_id": "unique identifier if mentioned or generate one",
        "link_id": "road link ID if mentioned",
        "incident_type": "accident/breakdown/roadworks/weather/other",
        "severity": "high/medium/low",
        "blocked_lanes": ["list", "of", "blocked", "lanes"],
        "queue_length": "length in meters (number only)",
        "time": "time in HHMM format",
        "duration_minutes": "how long incident has been active (number only)",
        "location_description": "human readable location",
        "additional_hazards": ["list", "of", "any", "additional", "hazards"],
        "weather_conditions": "if mentioned",
        "traffic_volume": "high/medium/low if assessable from time/location"
        "road_type": "major_roads/motorways/other_major_roads/secondary_roads/local_connecting_roads/local_roads_high_importance/local_roads/local_roads_minor_importance/other_roads (taken from incident link)"
    }}
    
    If information is not provided, use null for that field.
    Extract only factual information from the description.
    """
    
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error extracting event data: {str(e)}"

@tool
def analyze_event_changes(event_id: str, event_data: str) -> str:
    """
    Analyze changes between current and previous event states to determine if a response plan update is needed.
    
    Args:
        event_data: Current event data including incident details, lane closures, queue lengths
    
    Returns:
        JSON with analysis of changes and recommendation on whether to update the response plan
    """
    previous_data = None
    print("Analysing changes in event.")
    
    try:
        check_query = """
        MATCH (e:event_record {event_id: $event_id})
        RETURN e.event_id AS event_id
        """

        with driver.session() as session:
            existing = session.run(check_query, event_id=event_id).single()

            if existing:
                print("This is an ongoing event. Analyzing changes now.")

                result = session.run(
                    """
                    MATCH (n)
                    WHERE n.event_id = $event_id
                    RETURN n
                    """,
                    event_id=event_id
                )

                previous_data = [dict(record["n"]) for record in result]
                print(previous_data)

            else:
                print("This is a new event. Proceed to generate new response plan.")
                previous_data = None

        # Now build the prompt after previous_data is set
        prompt = f"""
        You are an expert traffic management analyst. Compare the current event data with previous data
        and determine if changes warrant updating the response plan.

        CURRENT EVENT DATA:
        {event_data}

        PREVIOUS EVENT DATA:
        {previous_data or "No previous data available - this is a new event."}

        ANALYSIS RULES:
        1. Lane Blockages: ANY change in lane closures = HIGH significance, update required
        2. Queue Length: >500m change = HIGH significance, 200-500m = MEDIUM, <200m = LOW  
        3. Incident Severity: ANY severity change = HIGH significance, update required
        4. Time Changes: >2 hours elapsed OR crossing rush hour periods = MEDIUM significance
        5. Additional Hazards: NEW hazards reported = HIGH significance, update required

        UPDATE DECISION LOGIC:
        - If ANY change has HIGH significance → update_required = TRUE
        - If 2+ changes have MEDIUM significance → update_required = TRUE  
        - If ALL changes are LOW significance → update_required = FALSE
        - If this is a new event (no previous data) → update_required = TRUE

        Return your analysis in the following JSON format:

        {{
            "event_id": "{event_id}",
            "is_update": {str(previous_data is not None).lower()},
            "update_required": true/false,
            "significant_changes": [
                {{
                    "metric": "lane_blockage/queue_length/severity/time/hazards",
                    "previous_value": "previous value if available",
                    "current_value": "current value",
                    "significance": "high/medium/low",
                    "reasoning": "Why this change matters or doesn't"
                }}
            ],
            "critical_changes": true/false,
            "recommendation": "Update response plan / No update needed",
            "explanation": "Detailed explanation based on the UPDATE DECISION LOGIC above"
        }}

        IMPORTANT: 
        - DO NOT return anything other than the JSON output 
        - NO additional explanations outside of JSON are require
        - Be strict about update_required - only set to TRUE if genuinely significant changes occurred
        - If no meaningful changes, set update_required = FALSE to avoid unnecessary plan generation
        - For new events (no previous data), always set update_required = TRUE
        """

        response = llm.invoke(prompt)
        return response.content

    except Exception as e:
        return f"Error analyzing event changes: {str(e)}"

    
@tool
def store_event_details(event_data: str, event_id: str, graph_schema: str = None) -> str:
    """
    Stores event details as an `event_record` node in Neo4j.

    Args:
        event_data: JSON string of structured event data.
        event_id: Unique identifier for the event.
        graph_schema: JSON string of the graph schema (optional, will use cached schema if not provided)

    Returns:
        Confirmation of storage with event ID.
    """
    try:
        print("Creating Event Record node in NEO4J now.")
        # Use provided schema or fall back to cached schema
        schema_to_use = graph_schema if graph_schema else str(CACHED_SCHEMA) if CACHED_SCHEMA else "Schema not available"
        
        prompt = f"""
        You are an expert in generating Neo4j Cypher queries.
        UTILIZE MERGE NOT CREATE FUNCTION WHEN UPDATING

        Use the schema below to:
        1. Create an `event_record` node.
        2. Use only the properties listed under the `event_record` node in the schema.
        3. Replace missing or unknown values with null.
        4. Add in additional property road_type taken from the incident link
        5. Use '{event_id}' as the event_id.
        6. Add a `created_timestamp` with datetime().
        7. End with: RETURN e.event_id AS event_id

        IMPORTANT RELATIONSHIP CREATION:
        - After creating the event_record, find the road link using the link_id from the event data
        - Create a CONNECTED_TO relationship: (event_record)-[:LOCATED_AT]->(road_link)
        - The road link should be matched by its link_id property (or similar identifier)

        SCHEMA: {schema_to_use}

        EVENT DATA:
        {event_data}

        Output ONLY a valid Cypher query. Do NOT include any explanation.
        """

        response = llm.invoke(prompt)

        with driver.session() as session:
            result = session.run(response.content)
            record = result.single()
            
            return f"Event stored successfully with ID: {record['event_id']}"


    except Exception as e:
        return f"Error storing event: {str(e)}" 


@tool
def store_event_plan(response_plan: str, event_id: str, vms_used: list = None) -> str:
    """
    Stores a response plan as an `event_plan` node in Neo4j and links it to the corresponding `event_record`.

    Args:
        response_plan: JSON string of the plan details.
        event_id: ID of the associated event.
        vms_used: list of EQT_NO of the vms used in the plan (optional, will extract from plan if not provided)

    Returns:
        Confirmation message with plan ID if available.
    """
    print("Creating Plan node in NEO4J now.")
    try:
        # Extract VMS IDs from response plan if not provided
        if not vms_used:
            try:
                print("VMS list not provided, extracting from plan now.")
                import json
                plan_data = json.loads(response_plan)
                vms_used = []
                
                # Extract from traffic_management_actions
                if 'traffic_management_actions' in plan_data:
                    for action in plan_data['traffic_management_actions']:
                        if 'eqt_no' in action and action['eqt_no']:
                            vms_used.append(action['eqt_no'])
                
                print(f"Extracted VMS IDs from plan: {vms_used}")
            except Exception as e:
                print(f"Could not extract VMS IDs from plan: {e}")
                vms_used = []

        # Create the main event_plan node first
        main_query = f"""
        MERGE (ep:event_plan {{event_id: '{event_id}'}})
        ON CREATE SET 
            ep.id = toString(randomUUID()),
            ep.created_timestamp = datetime(),
            ep.plan_status = 'active'
        SET ep.plan_details = $plan_data
        WITH ep
        MATCH (er:event_record {{event_id: '{event_id}'}})
        MERGE (er)-[:HAS_PLAN]->(ep)
        RETURN ep.id AS plan_id
        """

        with driver.session() as session:
            # Execute main query to create event_plan and link to event_record
            result = session.run(main_query, plan_data=response_plan)
            record = result.single()
            plan_id = record.get('plan_id', 'unknown') if record else 'unknown'
            
            # Create VMS relationships separately if VMS IDs exist
            vms_linked = 0
            if vms_used:
                for vms_id in vms_used:
                    try:
                        vms_query = """
                        MATCH (ep:event_plan {event_id: $event_id}), (vms:VMS {EQT_NO: $vms_id})
                        MERGE (vms)-[:CONTROLS_VMS]->(ep)
                        RETURN vms.EQT_NO AS linked_vms
                        """
                        vms_result = session.run(vms_query, event_id=event_id, vms_id=vms_id)
                        if vms_result.single():
                            vms_linked += 1
                            print(f"Successfully linked VMS {vms_id}")
                        else:
                            print(f"VMS {vms_id} not found in database")
                    except Exception as vms_error:
                        print(f"Error linking VMS {vms_id}: {vms_error}")
            
            return f"Response plan stored successfully with ID: {plan_id}. VMS linked: {vms_linked}/{len(vms_used)} devices"

    except Exception as e:
        print(f"Error details: {str(e)}")
        return f"Error storing plan: {str(e)}"

# Tools list for the workflow
tools = [get_schema, run_cypher_query, generate_response_plan, analyze_event_changes, extract_event_data, store_event_details, store_event_plan]
