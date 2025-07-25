"""Integration tests for Neo4j connectivity."""

import pytest
from unittest.mock import patch

@pytest.mark.integration
def test_neo4j_connection(neo4j_connection):
    """Test Neo4j database connection."""
    assert neo4j_connection is not None
    
    # Test basic connectivity
    with neo4j_connection.session() as session:
        result = session.run("RETURN 1 as test")
        record = result.single()
        assert record["test"] == 1

@pytest.mark.integration  
def test_schema_retrieval():
    """Test schema retrieval from Neo4j."""
    from src.tools.neo4j_tools import get_schema
    
    # This would require actual Neo4j connection
    # For integration test, we can mock it or use test database
    with patch('src.tools.neo4j_tools.get_neo4j_graph') as mock_graph:
        mock_graph.return_value.get_schema = "Test schema"
        
        result = get_schema.func()
        assert "Test schema" in result

@pytest.mark.integration
def test_cypher_query_execution():
    """Test actual Cypher query execution."""
    from src.tools.neo4j_tools import run_cypher_query
    
    # Test with simple query
    result = run_cypher_query.func("RETURN 1 as test")
    
    # Should not contain error message
    assert "Query error:" not in result
