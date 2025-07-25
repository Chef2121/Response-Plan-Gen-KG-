"""Event processing tools for traffic incident management."""

from langchain_core.tools import tool
from config.llm import get_llm


@tool
def extract_event_data(event_description: str) -> str:
    """
    Extract structured event data from user input or event updates.
    
    Args:
        event_description: Description of the traffic event or incident
    
    Returns:
        JSON with structured event data for comparison
    """
    
    prompt = f"""
    Extract structured data from this traffic event description:
    
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
    }}
    
    If information is not provided, use null for that field.
    Extract only factual information from the description.
    """
    
    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error extracting event data: {str(e)}"


@tool
def analyze_event_changes(event_data: str, previous_data: str = None) -> str:
    """
    Analyze changes between current and previous event states to determine if a response plan update is needed.
    
    Args:
        event_data: Current event data including incident details, lane closures, queue lengths
        previous_data: Previous event data for comparison (if available)
    
    Returns:
        JSON with analysis of changes and recommendation on whether to update the response plan
    """
    
    prompt = f"""
    You are an expert traffic management analyst. Compare the current event data with previous data
    and determine if changes warrant updating the response plan.
    
    CURRENT EVENT DATA:
    {event_data}
    
    PREVIOUS EVENT DATA:
    {previous_data or "No previous data available - this is a new event."}
    
    Analyze the following key metrics:
    1. Lane Blockages: Have lane closures changed? (most critical factor)
    2. Queue Length: Has queue length increased/decreased significantly? (>500m change is significant)
    3. Incident Severity: Has the incident severity changed?
    4. Time Changes: Has significant time elapsed affecting traffic conditions such as rush hour?
    5. Additional Hazards: Have new hazards been reported?
    
    Return your analysis in the following JSON format:
    
    {{
        "event_id": "Extract or generate unique identifier",
        "is_update": true/false,
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
        "explanation": "Detailed explanation of your recommendation"
    }}
    
    If this is a new event (no previous data), set 'update_required' = True.
    """
    
    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error analyzing event changes: {str(e)}"
