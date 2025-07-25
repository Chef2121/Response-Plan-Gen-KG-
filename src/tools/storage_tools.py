"""Storage tools for persisting events and plans to Neo4j."""

from langchain_core.tools import tool
from config.database import get_neo4j_driver
from config.llm import get_llm


@tool
def store_event_details(event_data: str, graph_schema: str) -> str:
    """
    Store the Event details as node in Neo4J Database

    Args:
        event_data: JSON string of structured event data
        schema: JSON string of the graph schema
    
    Returns:
        Confirmation of storage with event ID
    """
    try:
        prompt = f"""
        You are an expert in generating Neo4j graph cyphers.
        Strictly follow the schema below when creating new event nodes.
        
        SCHEMA:
        {graph_schema}
        
        EVENT DATA:
        {event_data}
        
        Requirements:
        1. Create an Event node with properties from the event_data
        2. Use only properties that exist in the schema
        3. Replace missing data with null
        4. Generate a unique event_id if not provided (use apoc.create.uuid() or timestamp)
        5. Add a created_timestamp with datetime()
        6. MUST include "RETURN e.event_id as event_id" at the end
        
        ONLY output a valid Cypher query with RETURN statement. DO NOT add other information.
        """

        llm = get_llm()
        response = llm.invoke(prompt)
        
        driver = get_neo4j_driver()
        with driver.session() as session:
            result = session.run(response.content)
            record = result.single()
            
            if record and 'event_id' in record:
                return f"Event stored successfully with ID: {record['event_id']}"
            else:
                # Fallback if no event_id returned
                return "Event stored successfully with ID: unknown"
        
    except Exception as e:
        return f"Error storing event: {str(e)}"


@tool
def store_event_plan(response_plan: str, event_id: str, graph_schema: str) -> str:
    """
    Stores the response plan as a node in Neo4j database and creates a relationship between respective event node and plan node

    Args: 
        response_plan: json string of the plan details
        event_id: string of the respective event id

    returns:
        A message confirming the success
    """
    try:
        prompt = f"""
        You are an expert in generating Neo4j graph cyphers.
        
        Create a Cypher query that:
        1. Creates a ResponsePlan node with properties from the response_plan data
        2. Connects it to the existing Event node with the given event_id
        3. Follows the schema structure below
        
        SCHEMA:
        {graph_schema}
        
        RESPONSE PLAN DATA:
        {response_plan}
        
        EVENT ID TO CONNECT TO:
        {event_id}
        
        Requirements:
        - Generate a unique plan_id using apoc.create.uuid() if available, or use a timestamp-based ID
        - Add a created_timestamp with datetime()
        - Create a HAS_RESPONSE_PLAN relationship between Event and ResponsePlan nodes
        - Only use properties that exist in the schema
        - Store complex objects (like traffic_management_actions) as JSON strings
        - Set plan status as 'active'
        
        ONLY output a valid Cypher query, DO NOT add other information.
        """

        llm = get_llm()
        response = llm.invoke(prompt)
        
        driver = get_neo4j_driver()
        with driver.session() as session:
            result = session.run(response.content)
            record = result.single()
            if record and 'plan_id' in record:
                return f"Response plan stored successfully with ID: {record['plan_id']}"
            else:
                return "Response plan stored successfully"
                
    except Exception as e:
        return f"Error storing plan: {str(e)}"
