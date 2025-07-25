"""Neo4j database tools for querying road network data."""

from langchain_core.tools import tool
from config.database import get_neo4j_driver, get_neo4j_graph


@tool
def run_cypher_query(query: str) -> str:
    """Execute a Cypher query against the Neo4j database to retrieve road network data.
    
    Use this tool when you need to:
    - Find specific roads, intersections, or traffic data
    - search for past event details either by the link id or the event id
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
        driver = get_neo4j_driver()
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
        graph = get_neo4j_graph()
        schema_info = graph.get_schema
        return str(schema_info)
    except Exception as e:
        return f"Schema error: {str(e)}"
