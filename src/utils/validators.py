"""Data validation utilities."""

import json
from typing import Dict, Any
from src.core.schemas import TrafficEvent, ResponsePlan


def validate_event_data(event_data: str) -> Dict[str, Any]:
    """Validate and parse event data JSON."""
    try:
        data = json.loads(event_data)
        # Validate using Pydantic model
        event = TrafficEvent(**data)
        return event.dict()
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    except Exception as e:
        raise ValueError(f"Event data validation failed: {e}")


def validate_response_plan(plan_data: str) -> Dict[str, Any]:
    """Validate and parse response plan JSON."""
    try:
        data = json.loads(plan_data)
        # Basic validation - ResponsePlan model would need adjustment for complex nested structures
        required_fields = ["plan_type", "priority", "estimated_duration", "traffic_management_actions"]
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    except Exception as e:
        raise ValueError(f"Response plan validation failed: {e}")


def sanitize_cypher_query(query: str) -> str:
    """Basic sanitization for Cypher queries."""
    # Remove potentially dangerous operations
    dangerous_keywords = ["DELETE", "REMOVE", "SET", "CREATE", "MERGE", "DROP"]
    
    for keyword in dangerous_keywords:
        if keyword.upper() in query.upper():
            raise ValueError(f"Dangerous operation '{keyword}' not allowed in query")
    
    return query.strip()
