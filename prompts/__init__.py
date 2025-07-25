"""
Prompts module for the RPG (Response Plan Generator) system.

This module contains all the prompts and guidelines used by the traffic incident
management system, including psychology-based messaging rules, database schema
documentation, and system prompts for the LLM agents.
"""

from .psychology_guidelines import psychology_guidelines
from .schema_docs import schema_docs
from .system_prompts import system_prompt

__all__ = [
    'psychology_guidelines',
    'schema_docs', 
    'system_prompt'
]