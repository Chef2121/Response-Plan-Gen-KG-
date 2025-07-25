"""Unit tests for agent classes."""

import pytest
from unittest.mock import Mock, patch

def test_road_network_chatbot_initialization():
    """Test chatbot initialization."""
    with patch('src.agents.traffic_agent.create_workflow') as mock_workflow:
        mock_workflow.return_value = Mock()
        
        from src.agents.traffic_agent import RoadNetworkChatBot
        
        chatbot = RoadNetworkChatBot(verbose=False)
        assert chatbot.verbose == False
        assert chatbot.app is not None

def test_chatbot_query():
    """Test basic query functionality."""
    with patch('src.agents.traffic_agent.create_workflow') as mock_workflow:
        mock_app = Mock()
        mock_response = Mock()
        mock_response.content = "Test response"
        
        mock_result = {
            "messages": [mock_response]
        }
        mock_app.invoke.return_value = mock_result
        mock_workflow.return_value = mock_app
        
        from src.agents.traffic_agent import RoadNetworkChatBot
        
        chatbot = RoadNetworkChatBot(verbose=False)
        result = chatbot.query("Test question")
        
        assert result == "Test response"

def test_chatbot_query_error_handling():
    """Test error handling in query method."""
    with patch('src.agents.traffic_agent.create_workflow') as mock_workflow:
        mock_app = Mock()
        mock_app.invoke.side_effect = Exception("Test error")
        mock_workflow.return_value = mock_app
        
        from src.agents.traffic_agent import RoadNetworkChatBot
        
        chatbot = RoadNetworkChatBot(verbose=False)
        result = chatbot.query("Test question")
        
        assert "Error:" in result
        assert "Test error" in result
