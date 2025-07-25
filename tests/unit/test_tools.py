"""Unit tests for tools modules."""

import pytest
import json
from unittest.mock import Mock, patch

def test_extract_event_data():
    """Test event data extraction."""
    from src.tools.event_tools import extract_event_data
    
    event_description = "Accident on link 17840006094278 at 0845, two lanes blocked"
    
    with patch('src.tools.event_tools.get_llm') as mock_llm:
        mock_response = Mock()
        mock_response.content = json.dumps({
            "link_id": "17840006094278",
            "incident_type": "accident", 
            "time": "0845",
            "blocked_lanes": ["lane1", "lane2"]
        })
        mock_llm.return_value.invoke.return_value = mock_response
        
        result = extract_event_data.func(event_description)
        
        assert "17840006094278" in result
        assert "accident" in result

def test_run_cypher_query():
    """Test Cypher query execution."""
    from src.tools.neo4j_tools import run_cypher_query
    
    with patch('src.tools.neo4j_tools.get_neo4j_driver') as mock_driver:
        mock_session = Mock()
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([{"test": "data"}]))
        mock_session.run.return_value = mock_result
        mock_driver.return_value.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.return_value.session.return_value.__exit__ = Mock(return_value=None)
        
        result = run_cypher_query.func("MATCH (n) RETURN n LIMIT 1")
        
        assert "test" in result

def test_generate_response_plan():
    """Test response plan generation."""
    from src.tools.plan_tools import generate_response_plan
    
    context = "Test incident context with VMS data"
    
    with patch('src.tools.plan_tools.get_llm') as mock_llm:
        mock_response = Mock()
        mock_response.content = json.dumps({
            "plan_type": "Traffic Management Plan",
            "priority": "High",
            "traffic_management_actions": []
        })
        mock_llm.return_value.invoke.return_value = mock_response
        
        result = generate_response_plan.func(context)
        
        assert "Traffic Management Plan" in result
