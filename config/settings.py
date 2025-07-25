"""Application settings and environment variable management."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # Neo4j Configuration
    NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME = os.environ.get("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
    
    # Anthropic API Key
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    
    # LangSmith Configuration
    LANGCHAIN_TRACING_V2 = os.environ.get("LANGCHAIN_TRACING_V2", "true")
    LANGCHAIN_ENDPOINT = os.environ.get("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    LANGCHAIN_API_KEY = os.environ.get("LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT = os.environ.get("LANGCHAIN_PROJECT", "traffic-management")
    
    # Application Settings
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
    
    def validate(self):
        """Validate required settings."""
        required_settings = [
            ("NEO4J_PASSWORD", self.NEO4J_PASSWORD),
            ("ANTHROPIC_API_KEY", self.ANTHROPIC_API_KEY)
        ]
        
        missing = [name for name, value in required_settings if not value]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


# Global settings instance
settings = Settings()
