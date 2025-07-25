"""Response plan generation tools."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_core.tools import tool
from config.llm import get_llm
from prompts.psychology_guidelines import psychology_guidelines


@tool 
def generate_response_plan(context: str) -> str:
    """
    Generates a response plan based on the incident context retrieved from the knowledge graph
    Input: context (string) - Comprehensive context including incident details, VMS data importantly the id,
    event with their respective plan and plan command history to provide context.
    Returns: the explicit JSON formatted response plan with actions and VMS commands not the summary.
    """
    
    prompt = f"""
    You are an expert in traffic management specializing in creating response plans.
    Based on traffic incident information and psychological principles, generate a comprehensive response plan.
    
    Context: {context}
    
    {psychology_guidelines}
    
    RESPONSE PLAN FORMAT:
    Generate a response plan in the following JSON format:

    {{
        "plan_type": "Traffic Management Plan",
        "priority": "High/Medium/Low",
        "estimated_duration": "X minutes/hours",
        "traffic_management_actions": [
            {{
                "eqt_no": "VMS_EQUIPMENT_ID (from EQT_NO or EQT_EXT_ID)",
                "message_line_1": "Primary message (max 20 chars)",
                "message_line_2": "Secondary message (max 20 chars)",
                "display_duration": "X minutes",
                "distance": "distance from event in meters",
                "psychological_rationale": "Why this message is psychologically effective",
                "behavioral_goal": "Desired driver behavior",
                "urgency_level": "High/Medium/Low based on distance and severity",
                "reasoning": "Give your reasoning for all of the above, why this duration etc."
            }},
            
            {{
                "action": "Specific action to take",
                "location": "Where to implement",
                "resources_needed": "What resources are required",
                "timing": "When to implement"
            }}
        ],
        "messaging_strategy": {{
            "primary_emotion": "Urgency/Caution/Information",
            "cognitive_approach": "Simple/Clear/Direct",
            "behavioral_target": "Slow down/Merge/Avoid area"
        }},
        "emergency_response": {{
            "agencies_to_notify": [
                {{
                    "agency": "Police/Fire Services/Emergency Medical Services/Road Maintenance/Traffic Control",
                    "priority": "Immediate/High/Medium/Low",
                    "reason": "Specific reason for notification",
                    "contact_method": "Emergency dispatch/Direct call/Radio",
                    "resources_requested": "Number of units/personnel needed"
                }}
            ],
            "coordination_requirements": "How agencies should coordinate",
            "scene_management": "Who takes lead and scene control responsibilities"
        }},
        "justification": "Psychology-based explanation of messaging choices"
    }}
    
    RECOMMENDED ACTIONS GUIDELINES:
    1. Generate additional actions that could aid in controlling the event
    2. Provide a priority level to recommended event
    3. Give clear reasoning and thought behind each event
    4. State the required equipment and personnel to carry out said action
    5. Recommend at least 2 actions

    EMERGENCY RESPONSE AGENCY GUIDELINES:
    1. POLICE: Required for all accidents with injuries, traffic control, investigation
    2. FIRE SERVICES: Required for vehicle fires, fuel spills, extraction operations
    3. EMERGENCY MEDICAL SERVICES: Required for any injuries, medical emergencies
    4. ROAD MAINTENANCE: Required for debris cleanup, road surface damage, barrier repairs
    5. TRAFFIC CONTROL: Required for major incidents affecting multiple lanes or extended duration
    6. TOWING SERVICES: Required for vehicle removal, clearance operations
    
    PRIORITY LEVELS:
    - Immediate: Life-threatening situations, major blockages during rush hour
    - High: Injuries present, significant traffic impact, hazardous conditions
    - Medium: Property damage only, minor traffic disruption, routine cleanup
    - Low: Minor incidents, off-peak hours, minimal impact
    
    PSYCHOLOGICAL MESSAGING RULES:
    1. Use psychology guidelines above to craft messages
    2. Consider time of day (0800 = rush hour psychology)
    3. Match message urgency to distance from incident
    4. Use action-oriented language that triggers immediate response
    5. Avoid cognitive overload - keep messages simple and clear
    6. Consider emotional state of stressed commuters

    Generate practical VMS messages that will effectively influence driver behavior and prevent secondary accidents.
    """
    
    try:
        llm = get_llm()
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"Error generating psychology-based response plan: {str(e)}"
