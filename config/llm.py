"""LLM configuration and initialization."""

from langchain_anthropic import ChatAnthropic
from .settings import settings

llm = ChatAnthropic(
            model="claude-3-5-haiku-latest",
            temperature=0.3,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=4000
        )

def get_llm():
    """Initialize and return the ChatAnthropic LLM instance."""
    try:
        return llm
        
    except Exception as e:
        print(f"LLM initialization failed: {e}")
        raise
