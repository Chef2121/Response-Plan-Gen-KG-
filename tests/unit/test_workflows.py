"""Unit tests for workflow components."""

import pytest
from unittest.mock import Mock, patch

def test_should_continue_with_tool_calls():
    """Test routing logic when tool calls are present."""
    from src.workflows.routing import should_continue
    
    mock_message = Mock()
    mock_message.tool_calls = [{"name": "test_tool"}]
    
    state = {
        "messages": [mock_message],
        "needs_revision": False
    }
    
    result = should_continue(state)
    assert result == "tools"

def test_route_after_human_feedback_approved():
    """Test routing after human approval."""
    from src.workflows.routing import route_after_human_feedback
    from langgraph.graph import END
    
    state = {
        "final_approved": True,
        "user_feedback": "approve"
    }
    
    result = route_after_human_feedback(state)
    assert result == END

def test_route_after_human_feedback_rejected():
    """Test routing after human rejection."""
    from src.workflows.routing import route_after_human_feedback
    
    state = {
        "final_approved": False,
        "user_feedback": "needs changes"
    }
    
    result = route_after_human_feedback(state)
    assert result == "agent"

def test_call_model_basic():
    """Test basic model calling."""
    from src.workflows.nodes import call_model
    from langchain_core.messages import HumanMessage
    
    state = {
        "messages": [HumanMessage(content="test message")],
        "user_feedback": "",
        "needs_revision": False,
        "current_plan": ""
    }
    
    with patch('src.workflows.nodes.get_llm') as mock_llm:
        mock_response = Mock()
        mock_response.content = "Test response"
        mock_llm.return_value.bind_tools.return_value.invoke.return_value = mock_response
        
        result = call_model(state)
        
        assert "messages" in result
        assert result["needs_revision"] == False
