"""End-to-end system tests."""

import pytest
from unittest.mock import Mock, patch

@pytest.mark.e2e
def test_complete_workflow(sample_event_data):
    """Test complete traffic incident workflow."""
    from src.agents.traffic_agent import RoadNetworkChatBot
    
    # Mock the entire workflow
    with patch('src.agents.traffic_agent.create_workflow') as mock_workflow:
        mock_app = Mock()
        
        # Mock successful workflow completion
        mock_response = Mock()
        mock_response.content = "Response plan generated successfully"
        
        mock_result = {
            "messages": [mock_response],
            "final_approved": True
        }
        mock_app.invoke.return_value = mock_result
        mock_workflow.return_value = mock_app
        
        chatbot = RoadNetworkChatBot(verbose=False)
        
        incident_query = f"Event at link {sample_event_data['link_id']} with {sample_event_data['severity']} severity"
        result = chatbot.query(incident_query)
        
        assert "successfully" in result.lower()

@pytest.mark.e2e
def test_human_feedback_loop():
    """Test human feedback integration."""
    from src.workflows.nodes import human_feedback
    
    # Mock human input
    with patch('builtins.input', return_value='approve'):
        state = {
            "messages": [Mock()],
            "revision_count": 0
        }
        
        result = human_feedback(state)
        
        assert result["final_approved"] == True
        assert result["user_feedback"] == "approve"

@pytest.mark.e2e 
def test_error_recovery():
    """Test system error recovery."""
    from src.agents.traffic_agent import RoadNetworkChatBot
    
    with patch('src.agents.traffic_agent.create_workflow') as mock_workflow:
        mock_app = Mock()
        # First call fails, second succeeds
        mock_app.invoke.side_effect = [Exception("Temporary error"), {"messages": [Mock()]}]
        mock_workflow.return_value = mock_app
        
        chatbot = RoadNetworkChatBot(verbose=False)
        
        # First attempt should return error
        result = chatbot.query("Test query")
        assert "Error:" in result
