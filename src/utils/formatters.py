"""Response formatting utilities."""

import json
from typing import Dict, Any


def format_response_plan(plan_data: Dict[str, Any]) -> str:
    """Format response plan for display."""
    formatted = "🚦 TRAFFIC MANAGEMENT RESPONSE PLAN\n"
    formatted += "=" * 50 + "\n\n"
    
    formatted += f"Plan Type: {plan_data.get('plan_type', 'N/A')}\n"
    formatted += f"Priority: {plan_data.get('priority', 'N/A')}\n"
    formatted += f"Estimated Duration: {plan_data.get('estimated_duration', 'N/A')}\n\n"
    
    # VMS Actions
    actions = plan_data.get('traffic_management_actions', [])
    if actions:
        formatted += "📺 VMS ACTIONS:\n"
        formatted += "-" * 20 + "\n"
        for i, action in enumerate(actions, 1):
            if isinstance(action, dict) and 'eqt_no' in action:
                formatted += f"{i}. Equipment: {action.get('eqt_no', 'N/A')}\n"
                formatted += f"   Message: {action.get('message_line_1', '')} | {action.get('message_line_2', '')}\n"
                formatted += f"   Duration: {action.get('display_duration', 'N/A')}\n"
                formatted += f"   Distance: {action.get('distance', 'N/A')}\n\n"
    
    # Emergency Response
    emergency = plan_data.get('emergency_response', {})
    if emergency:
        formatted += "🚨 EMERGENCY RESPONSE:\n"
        formatted += "-" * 20 + "\n"
        agencies = emergency.get('agencies_to_notify', [])
        for agency in agencies:
            if isinstance(agency, dict):
                formatted += f"• {agency.get('agency', 'N/A')} - {agency.get('priority', 'N/A')} priority\n"
                formatted += f"  Reason: {agency.get('reason', 'N/A')}\n\n"
    
    return formatted


def format_vms_list(vms_data: list) -> str:
    """Format VMS equipment list for display."""
    if not vms_data:
        return "No VMS equipment found."
    
    formatted = "📺 VMS EQUIPMENT FOUND:\n"
    formatted += "=" * 30 + "\n"
    
    for i, vms in enumerate(vms_data, 1):
        formatted += f"{i}. Equipment ID: {vms.get('EQT_NO', vms.get('EQT_EXT_ID', 'N/A'))}\n"
        formatted += f"   Road: {vms.get('ROAD_NAME', 'N/A')}\n"
        formatted += f"   Distance: {vms.get('distance_meters', 'N/A')} meters\n"
        formatted += f"   Location: {vms.get('LATITUDE', 'N/A')}, {vms.get('LONGITUDE', 'N/A')}\n\n"
    
    return formatted


def format_json_response(data: Any) -> str:
    """Format JSON data for readable display."""
    try:
        if isinstance(data, str):
            data = json.loads(data)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except:
        return str(data)
