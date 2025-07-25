"""Graph state definition for the LangGraph workflow."""

from typing import TypedDict, List, Annotated
from langchain_core.messages import HumanMessage, AIMessage
import operator


class GraphState(TypedDict):
    """State object for the traffic management workflow."""
    
    messages: Annotated[List[HumanMessage | AIMessage], operator.add]
    tool_calls: List[dict]
    user_feedback: str
    final_approved: bool
    revision_count: int
    needs_revision: bool
    current_plan: str
    event_history: List[dict]
    event_id: str
    previous_event_state: str
    current_event_state: str
    event_analysis_completed: bool
    update_required: bool
