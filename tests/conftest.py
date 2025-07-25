"""Pytest configuration and fixtures."""

import pytest
import os
from dotenv import load_dotenv

# Load test environment variables
load_dotenv()

@pytest.fixture(scope="session")
def neo4j_connection():
    """Provide Neo4j connection for tests."""
    from config.database import get_neo4j_driver
    driver = get_neo4j_driver()
    yield driver
    driver.close()

@pytest.fixture(scope="session")
def llm_instance():
    """Provide LLM instance for tests."""
    from config.llm import get_llm
    return get_llm()

@pytest.fixture
def sample_event_data():
    """Sample event data for testing."""
    return {
        "event_id": "test_event_123",
        "link_id": "17840006094278",
        "incident_type": "accident",
        "severity": "medium",
        "blocked_lanes": ["left", "center"],
        "queue_length": 750,
        "time": "0845",
        "duration_minutes": 35,
        "location_description": "Near Elmwood Avenue junction",
        "additional_hazards": ["spilled fuel", "debris"],
        "weather_conditions": "foggy",
        "traffic_volume": "high"
    }

@pytest.fixture
def sample_vms_data():
    """Sample VMS data for testing."""
    return [
        {
            "EQT_NO": "VMS001",
            "EQT_EXT_ID": "VMS001_EXT",
            "ROAD_NAME": "Main Highway",
            "LATITUDE": 25.123456,
            "LONGITUDE": 55.987654,
            "distance_meters": 500,
            "hops_from_incident": 2
        },
        {
            "EQT_NO": "VMS002", 
            "EQT_EXT_ID": "VMS002_EXT",
            "ROAD_NAME": "Main Highway",
            "LATITUDE": 25.123456,
            "LONGITUDE": 55.987654,
            "distance_meters": 1200,
            "hops_from_incident": 5
        }
    ]
