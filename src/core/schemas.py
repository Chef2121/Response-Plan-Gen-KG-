"""Data models and schemas for traffic management system."""

from typing import List, Optional, Literal
from pydantic import BaseModel


class TrafficEvent(BaseModel):
    """Traffic event data model."""
    
    event_id: Optional[str] = None
    link_id: Optional[str] = None
    incident_type: Literal["accident", "breakdown", "roadworks", "weather", "other"]
    severity: Literal["high", "medium", "low"]
    blocked_lanes: List[str]
    queue_length: Optional[int] = None  # meters
    time: Optional[str] = None  # HHMM format
    duration_minutes: Optional[int] = None
    location_description: Optional[str] = None
    additional_hazards: List[str] = []
    weather_conditions: Optional[str] = None
    traffic_volume: Optional[Literal["high", "medium", "low"]] = None


class VMSAction(BaseModel):
    """VMS action data model."""
    
    eqt_no: str
    message_line_1: str
    message_line_2: str
    display_duration: str
    distance: str
    psychological_rationale: str
    behavioral_goal: str
    urgency_level: Literal["High", "Medium", "Low"]
    reasoning: str


class EmergencyAgency(BaseModel):
    """Emergency response agency data model."""
    
    agency: str
    priority: Literal["Immediate", "High", "Medium", "Low"]
    reason: str
    contact_method: str
    resources_requested: str


class ResponsePlan(BaseModel):
    """Response plan data model."""
    
    plan_type: str
    priority: Literal["High", "Medium", "Low"]
    estimated_duration: str
    traffic_management_actions: List[VMSAction]
    messaging_strategy: dict
    emergency_response: dict
    justification: str
