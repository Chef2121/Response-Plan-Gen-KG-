"""LLM configuration and initialization."""

from langchain_anthropic import ChatAnthropic
from .settings import settings


def get_llm():
    """Initialize and return the ChatAnthropic LLM instance."""
    try:
        llm = ChatAnthropic(
            model="claude-3-5-haiku-latest",
            temperature=0.3,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=4000
        )
        print("LLM initialized successfully")
        return llm
        
    except Exception as e:
        print(f"LLM initialization failed: {e}")
        raise
