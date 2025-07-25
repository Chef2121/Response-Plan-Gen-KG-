"""Neo4j database configuration and connection management."""

import os
from neo4j import GraphDatabase
from langchain_neo4j import Neo4jGraph
from .settings import settings


class Neo4jConnection:
    """Manages Neo4j database connections."""
    
    def __init__(self):
        self.driver = None
        self.graph = None
    
    def connect(self):
        """Establish connection to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
            )
            
            # Verify connectivity
            self.driver.verify_connectivity()
            print("Neo4j connection successful")
            
            # Create LangChain Neo4j graph
            self.graph = Neo4jGraph(
                url=settings.NEO4J_URI,
                username=settings.NEO4J_USERNAME,
                password=settings.NEO4J_PASSWORD,
                timeout=30
            )
            
            return True
            
        except Exception as e:
            print(f"Neo4j setup failed: {e}")
            raise
    
    def close(self):
        """Close database connections."""
        if self.driver:
            self.driver.close()
    
    def get_session(self):
        """Get a database session."""
        if not self.driver:
            self.connect()
        return self.driver.session()


# Global connection instance
neo4j_connection = Neo4jConnection()


def get_neo4j_driver():
    """Get the Neo4j driver instance."""
    if not neo4j_connection.driver:
        neo4j_connection.connect()
    return neo4j_connection.driver


def get_neo4j_graph():
    """Get the LangChain Neo4j graph instance."""
    if not neo4j_connection.graph:
        neo4j_connection.connect()
    return neo4j_connection.graph
