from flask import Flask, request, render_template_string, jsonify, session
from rpg2 import RoadNetworkChatBot
import sys
from io import StringIO
import contextlib
import threading
import time
import uuid
import json
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production
chatbot = RoadNetworkChatBot()

# Global variable to track progress and manage sessions
progress_status = {}
active_sessions = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Response Plan Generator</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background-color: #f8f9fa;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .input-section {
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }
        textarea { 
            width: 100%; 
            max-width: 100%; 
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-family: Arial, sans-serif;
            resize: vertical;
        }
        .response { 
            background-color: #e8f5e8; 
            padding: 15px; 
            border-radius: 5px; 
            white-space: pre-wrap; 
            word-wrap: break-word;
            margin-bottom: 20px;
            border-left: 4px solid #28a745;
        }
        .plan-display {
            background-color: #fff3cd;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #ffc107;
            font-family: monospace;
            font-size: 14px;
            overflow-x: auto;
        }
        .human-feedback-section {
            background-color: #e3f2fd;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #2196f3;
        }
        .feedback-input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .observations {
            background-color: #fff3cd;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #ffc107;
        }
        .observation-step {
            margin-bottom: 15px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 3px;
        }
        .verbose { 
            background-color: #e8f4f8; 
            padding: 15px; 
            border-radius: 5px; 
            white-space: pre-wrap; 
            word-wrap: break-word;
            font-family: monospace;
            font-size: 12px;
            border-left: 4px solid #007acc;
        }
        .toggle-btn {
            background-color: #007acc;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
            font-size: 14px;
        }
        .toggle-btn:hover {
            background-color: #0056b3;
        }
        .progress-container {
            width: 100%;
            max-width: 100%;
            margin: 20px 0;
            display: none;
        }
        .progress-bar {
            width: 100%;
            height: 25px;
            background-color: #e0e0e0;
            border-radius: 12px;
            overflow: hidden;
            position: relative;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #007acc, #4fc3f7);
            border-radius: 12px;
            transition: width 0.3s ease;
            width: 0%;
        }
        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 13px;
            font-weight: bold;
            color: #333;
        }
        .progress-message {
            margin-top: 10px;
            font-size: 14px;
            color: #666;
            text-align: center;
        }
        .btn-primary {
            background-color: #007acc;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-right: 10px;
        }
        .btn-primary:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .btn-success {
            background-color: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            margin-right: 10px;
        }
        .btn-warning {
            background-color: #ffc107;
            color: #212529;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        .status-indicator {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-weight: bold;
        }
        .status-waiting {
            background-color: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        .status-approved {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status-rejected {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .workflow-step {
            background-color: #f8f9fa;
            border-left: 4px solid #6c757d;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
        }
        .workflow-step.active {
            border-left-color: #007acc;
            background-color: #e3f2fd;
        }
        .workflow-step.completed {
            border-left-color: #28a745;
            background-color: #e8f5e8;
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        h2 {
            color: #007acc;
            border-bottom: 2px solid #007acc;
            padding-bottom: 10px;
        }
        h3 {
            color: #6c757d;
            margin-top: 20px;
        }
    </style>
    <script>
        let progressInterval;
        let sessionId = '{{ session_id }}';
        
        function updateProgress() {
            fetch('/progress/' + sessionId)
                .then(response => response.json())
                .then(data => {
                    const progressBar = document.getElementById('progress-fill');
                    const progressText = document.getElementById('progress-text');
                    const progressMessage = document.getElementById('progress-message');
                    
                    if (progressBar && progressText && progressMessage) {
                        progressBar.style.width = data.progress + '%';
                        progressText.textContent = data.progress + '%';
                        progressMessage.textContent = data.message;
                    }
                    
                    if (data.status === 'waiting_feedback') {
                        clearInterval(progressInterval);
                        document.getElementById('progress-container').style.display = 'none';
                        document.getElementById('submit-btn').disabled = false;
                        // Reload to show the response plan and feedback form
                        location.reload();
                    } else if (data.status === 'complete' || data.status === 'error') {
                        clearInterval(progressInterval);
                        document.getElementById('progress-container').style.display = 'none';
                        document.getElementById('submit-btn').disabled = false;
                        if (data.status === 'complete') {
                            location.reload();
                        }
                    }
                });
        }
        
        function submitForm() {
            const submitBtn = document.getElementById('submit-btn');
            const progressContainer = document.getElementById('progress-container');
            
            submitBtn.disabled = true;
            progressContainer.style.display = 'block';
            
            // Start progress updates
            progressInterval = setInterval(updateProgress, 1000);
            
            // Submit the form
            document.getElementById('main-form').submit();
        }
        
        function submitFeedback(approved) {
            const feedbackText = document.getElementById('feedback-text').value;
            const feedbackForm = document.getElementById('feedback-form');
            
            // Create hidden inputs for the feedback
            const approvedInput = document.createElement('input');
            approvedInput.type = 'hidden';
            approvedInput.name = 'approved';
            approvedInput.value = approved;
            
            const feedbackInput = document.createElement('input');
            feedbackInput.type = 'hidden';
            feedbackInput.name = 'feedback_text';
            feedbackInput.value = feedbackText;
            
            feedbackForm.appendChild(approvedInput);
            feedbackForm.appendChild(feedbackInput);
            
            // Start progress tracking for feedback processing
            document.getElementById('progress-container').style.display = 'block';
            progressInterval = setInterval(updateProgress, 1000);
            
            feedbackForm.submit();
        }
        
        function toggleVerbose() {
            var element = document.getElementById("verbose-output");
            var button = document.getElementById("toggle-btn");
            if (element.style.display === "none") {
                element.style.display = "block";
                button.textContent = "Hide Debug Info";
            } else {
                element.style.display = "none";
                button.textContent = "Show Debug Info";
            }
        }
        
        function toggleObservations() {
            var element = document.getElementById("observations-output");
            var button = document.getElementById("toggle-obs-btn");
            if (element.style.display === "none") {
                element.style.display = "block";
                button.textContent = "Hide Observations";
            } else {
                element.style.display = "none";
                button.textContent = "Show Observations";
            }
        }
        
        function togglePlan() {
            var element = document.getElementById("plan-output");
            var button = document.getElementById("toggle-plan-btn");
            if (element.style.display === "none") {
                element.style.display = "block";
                button.textContent = "Hide Response Plan";
            } else {
                element.style.display = "none";
                button.textContent = "Show Response Plan";
            }
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>🚦 Response Plan Generator</h1>
        <p style="text-align: center; color: #6c757d; margin-bottom: 30px;">
            Human-in-the-loop traffic incident response planning system
        </p>
        
        {% if not waiting_feedback and not final_result %}
        <div class="input-section">
            <h2>📝 Incident Details</h2>
            <form id="main-form" method="post">
                <label for="user_input"><strong>Enter your question or incident details:</strong></label>
                <br><br>
                <textarea id="user_input" name="user_input" rows="4" placeholder="Example: There's a major accident on link 17840002118812 at 0800 hours with multiple vehicles involved and injuries reported."></textarea>
                <br><br>
                <button type="button" id="submit-btn" class="btn-primary" onclick="submitForm()">🔍 Generate Response Plan</button>
            </form>
        </div>
        {% endif %}
        
        <div id="progress-container" class="progress-container">
            <div class="progress-bar">
                <div id="progress-fill" class="progress-fill"></div>
                <div id="progress-text" class="progress-text">0%</div>
            </div>
            <div id="progress-message" class="progress-message">Initializing...</div>
        </div>
        
        {% if waiting_feedback %}
        <div class="status-indicator status-waiting">
            ⏳ <strong>Human Review Required</strong> - Please review the response plan below and provide feedback
        </div>
        
        <div class="workflow-step completed">
            <strong>Step 1:</strong> ✅ AI Analysis Complete - Found VMS equipment and generated response plan
        </div>
        <div class="workflow-step active">
            <strong>Step 2:</strong> 🔍 Human Review - Please evaluate the response plan
        </div>
        <div class="workflow-step">
            <strong>Step 3:</strong> 📋 Final Implementation - Apply approved plan
        </div>
        
        {% if response_plan %}
        <h2>📋 Generated Response Plan</h2>
        <button id="toggle-plan-btn" class="toggle-btn" onclick="togglePlan()">Hide Response Plan</button>
        <div id="plan-output" class="plan-display">{{ response_plan | safe }}</div>
        {% endif %}
        
        <div class="human-feedback-section">
            <h2>💬 Human Feedback</h2>
            <form id="feedback-form" method="post">
                <label for="feedback-text"><strong>Review the response plan and provide feedback:</strong></label>
                <br><br>
                <textarea id="feedback-text" name="feedback_text" rows="4" class="feedback-input" 
                          placeholder="Enter your feedback here. If you approve, you can leave this blank and click 'Approve'. If you want changes, please specify what needs to be modified."></textarea>
                <br>
                <button type="button" class="btn-success" onclick="submitFeedback(true)">✅ Approve Plan</button>
                <button type="button" class="btn-warning" onclick="submitFeedback(false)">🔄 Request Changes</button>
            </form>
            <p style="margin-top: 15px; color: #6c757d; font-size: 14px;">
                <strong>Tip:</strong> If you approve, the plan will be finalized. If you request changes, please provide specific feedback about what needs to be modified.
            </p>
        </div>
        {% endif %}
        
        {% if final_result %}
        {% if approved %}
        <div class="status-indicator status-approved">
            ✅ <strong>Plan Approved!</strong> - Response plan has been finalized and is ready for implementation
        </div>
        {% else %}
        <div class="status-indicator status-rejected">
            🔄 <strong>Plan Revised</strong> - Response plan has been updated based on your feedback
        </div>
        {% endif %}
        
        <div class="workflow-step completed">
            <strong>Step 1:</strong> ✅ AI Analysis Complete
        </div>
        <div class="workflow-step completed">
            <strong>Step 2:</strong> ✅ Human Review Complete
        </div>
        <div class="workflow-step completed">
            <strong>Step 3:</strong> ✅ Final Implementation Ready
        </div>
        
        {% if final_plan %}
        <h2>📋 Final Response Plan</h2>
        <button id="toggle-plan-btn" class="toggle-btn" onclick="togglePlan()">Hide Response Plan</button>
        <div id="plan-output" class="plan-display">{{ final_plan | safe }}</div>
        {% endif %}
        
        <div style="text-align: center; margin-top: 30px;">
            <button onclick="location.reload()" class="btn-primary">🔄 Start New Incident</button>
        </div>
        {% endif %}
        
        {% if observations %}
        <hr>
        <button id="toggle-obs-btn" class="toggle-btn" onclick="toggleObservations()">Show Agent Observations</button>
        <div id="observations-output" class="observations" style="display: none;">
            <h3>🤖 Agent Observations</h3>
            {{ observations | safe }}
        </div>
        {% endif %}
        
        {% if verbose_output %}
        <button id="toggle-btn" class="toggle-btn" onclick="toggleVerbose()">Show Debug Info</button>
        <div id="verbose-output" class="verbose" style="display: none;">
            <h3>🔧 Debug Information</h3>
            {{ verbose_output }}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

def update_progress(session_id, progress, message):
    """Update progress for a specific session"""
    if session_id not in progress_status:
        progress_status[session_id] = {}
    progress_status[session_id]["progress"] = progress
    progress_status[session_id]["message"] = message

def format_distance(distance_value):
    """Format distance with color coding and validation."""
    if not distance_value or distance_value == 'N/A':
        return 'N/A'
    
    try:
        # Try to extract numeric value
        numbers = re.findall(r'\d+', str(distance_value))
        if numbers:
            dist_value = int(numbers[0])
            
            # Format distance with proper units
            if 'meter' not in str(distance_value).lower():
                formatted_distance = f"{dist_value} meters"
            else:
                formatted_distance = str(distance_value)
            
            # Apply color coding based on distance ranges
            if dist_value == 0:
                return f"<span style='color: #dc3545; font-weight: bold;'>{formatted_distance} (ON INCIDENT LINK)</span>"
            elif dist_value < 500:
                return f"<span style='color: #dc3545; font-weight: bold;'>{formatted_distance} (IMMEDIATE PROXIMITY)</span>"
            elif dist_value < 1000:
                return f"<span style='color: #ffc107; font-weight: bold;'>{formatted_distance} (CLOSE RANGE)</span>"
            elif dist_value < 2000:
                return f"<span style='color: #28a745; font-weight: bold;'>{formatted_distance} (MEDIUM RANGE)</span>"
            else:
                return f"<span style='color: #6c757d; font-weight: bold;'>{formatted_distance} (FAR RANGE)</span>"
        else:
            return str(distance_value)
    except:
        return str(distance_value)

def format_response_plan(plan_text):
    """Format the response plan for better readability in the web UI."""
    if not plan_text or plan_text == "No plan found":
        return plan_text
    
    try:
        # Try to extract JSON from the text
        json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                # Parse and pretty-print the JSON
                parsed_json = json.loads(json_str)
                formatted_json = json.dumps(parsed_json, indent=2, ensure_ascii=False)
                
                # Create a more readable HTML format
                html_output = f"""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="color: #007acc; margin-top: 0;">📋 Response Plan Details</h3>
                    <div style="background-color: white; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745;">
                        <p><strong>Plan Type:</strong> {parsed_json.get('plan_type', 'N/A')}</p>
                        <p><strong>Priority:</strong> <span style="color: {'#dc3545' if parsed_json.get('priority') == 'High' else '#ffc107' if parsed_json.get('priority') == 'Medium' else '#28a745'}; font-weight: bold;">{parsed_json.get('priority', 'N/A')}</span></p>
                        <p><strong>Estimated Duration:</strong> {parsed_json.get('estimated_duration', 'N/A')}</p>
                    </div>
                </div>
                
                <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="color: #28a745; margin-top: 0;">🚦 VMS Actions</h3>
                    {"".join([f'''
                    <div style="background-color: white; padding: 15px; border-radius: 5px; margin-bottom: 15px; border-left: 4px solid #007acc;">
                        <h4 style="color: #007acc; margin-top: 0;">VMS Equipment: {action.get('eqt_no', 'N/A')}</h4>
                        <div style="background-color: #000; color: #00ff00; padding: 10px; border-radius: 3px; font-family: monospace; text-align: center; margin-bottom: 10px;">
                            <div style="font-size: 18px; font-weight: bold;">{action.get('message_line_1', '')}</div>
                            <div style="font-size: 18px; font-weight: bold;">{action.get('message_line_2', '')}</div>
                        </div>
                        <p><strong>📍 Distance from Incident:</strong> {format_distance(action.get('distance', 'N/A'))}</p>
                        <p><strong>⏱️ Display Duration:</strong> {action.get('display_duration', 'N/A')} minutes</p>
                        <p><strong>🎯 Behavioral Goal:</strong> {action.get('behavioral_goal', 'N/A')}</p>
                        <p><strong>🧠 Psychological Rationale:</strong> {action.get('psychological_rationale', 'N/A')}</p>
                        <p><strong>🚨 Urgency Level:</strong> <span style="color: {'#dc3545' if action.get('urgency_level') == 'High' else '#ffc107' if action.get('urgency_level') == 'Medium' else '#28a745'}; font-weight: bold;">{action.get('urgency_level', 'N/A')}</span></p>
                        <p><strong>💭 Reasoning:</strong> {action.get('reasoning', 'N/A')}</p>
                        <p><strong>🗺️ Link ID:</strong> {action.get('link_id', 'N/A')}</p>
                    </div>
                    ''' if action.get('eqt_no') else f'''
                    <div style="background-color: white; padding: 15px; border-radius: 5px; margin-bottom: 15px; border-left: 4px solid #17a2b8;">
                        <h4 style="color: #17a2b8; margin-top: 0;">🎯 Recommended Action</h4>
                        <p><strong>🔧 Action:</strong> {action.get('action', 'N/A')}</p>
                        <p><strong>📍 Location:</strong> {action.get('location', 'N/A')}</p>
                        <p><strong>🛠️ Resources Needed:</strong> {action.get('resources_needed', 'N/A')}</p>
                        <p><strong>⏰ Timing:</strong> {action.get('timing', 'N/A')}</p>
                    </div>
                    ''' for action in parsed_json.get('traffic_management_actions', [])])}
                </div>
                
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="color: #856404; margin-top: 0;">🎯 Messaging Strategy</h3>
                    <div style="background-color: white; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                        <p><strong>Primary Emotion:</strong> {parsed_json.get('messaging_strategy', {}).get('primary_emotion', 'N/A')}</p>
                        <p><strong>Cognitive Approach:</strong> {parsed_json.get('messaging_strategy', {}).get('cognitive_approach', 'N/A')}</p>
                        <p><strong>Behavioral Target:</strong> {parsed_json.get('messaging_strategy', {}).get('behavioral_target', 'N/A')}</p>
                    </div>
                </div>
                
                <div style="background-color: #f8d7da; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="color: #721c24; margin-top: 0;">🚨 Emergency Response</h3>
                    {"".join([f'''
                    <div style="background-color: white; padding: 15px; border-radius: 5px; margin-bottom: 15px; border-left: 4px solid #dc3545;">
                        <h4 style="color: #dc3545; margin-top: 0;">🚔 {agency.get('agency', 'N/A')}</h4>
                        <p><strong>Priority:</strong> <span style="color: {'#dc3545' if agency.get('priority') == 'Immediate' else '#ffc107' if agency.get('priority') == 'High' else '#28a745'}; font-weight: bold;">{agency.get('priority', 'N/A')}</span></p>
                        <p><strong>Reason:</strong> {agency.get('reason', 'N/A')}</p>
                        <p><strong>Contact Method:</strong> {agency.get('contact_method', 'N/A')}</p>
                        <p><strong>Resources Requested:</strong> {agency.get('resources_requested', 'N/A')}</p>
                    </div>
                    ''' for agency in parsed_json.get('emergency_response', {}).get('agencies_to_notify', [])])}
                    
                    <div style="background-color: white; padding: 15px; border-radius: 5px; border-left: 4px solid #6c757d;">
                        <p><strong>🤝 Coordination Requirements:</strong> {parsed_json.get('emergency_response', {}).get('coordination_requirements', 'N/A')}</p>
                        <p><strong>👮 Scene Management:</strong> {parsed_json.get('emergency_response', {}).get('scene_management', 'N/A')}</p>
                    </div>
                </div>
                
                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="color: #1976d2; margin-top: 0;">📝 Justification</h3>
                    <div style="background-color: white; padding: 15px; border-radius: 5px; border-left: 4px solid #2196f3;">
                        <p>{parsed_json.get('justification', 'N/A')}</p>
                    </div>
                </div>
                
                <details style="margin-top: 20px;">
                    <summary style="cursor: pointer; background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-weight: bold;">📄 Raw JSON (Click to expand)</summary>
                    <pre style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; margin-top: 10px;"><code>{formatted_json}</code></pre>
                </details>
                """
                
                return html_output
                
            except json.JSONDecodeError:
                # If JSON parsing fails, return formatted text
                return f"<pre style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap;'>{plan_text}</pre>"
        else:
            # If no JSON found, return formatted text
            return f"<pre style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap;'>{plan_text}</pre>"
            
    except Exception as e:
        # If any error occurs, return the original text
        return f"<pre style='background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap;'>{plan_text}</pre>"

@contextlib.contextmanager
def capture_stdout():
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    try:
        yield captured_output
    finally:
        sys.stdout = old_stdout

@app.route("/progress/<session_id>")
def get_progress(session_id):
    if session_id in progress_status:
        return jsonify(progress_status[session_id])
    return jsonify({"progress": 0, "status": "idle", "message": "No session found"})

def process_request_async(session_id, user_input):
    """Process the initial request asynchronously"""
    try:
        progress_status[session_id] = {"progress": 0, "status": "processing", "message": "Initializing..."}
        
        update_progress(session_id, 10, "Starting RPG2 agent...")
        
        # Capture verbose output
        with capture_stdout() as output:
            update_progress(session_id, 30, "Analyzing incident and searching for VMS equipment...")
            
            # Use the interrupt-based query method
            result, config, response_plan = chatbot.query_with_interrupt(user_input, thread_id=session_id)
            
            update_progress(session_id, 60, "Processing workflow...")
            
            # Check if we got a response plan (indicating we hit the interrupt)
            if response_plan:
                update_progress(session_id, 90, "Response plan ready for human review...")
                progress_status[session_id]["status"] = "waiting_feedback"
                progress_status[session_id]["response_plan"] = format_response_plan(response_plan)
                progress_status[session_id]["config"] = config
                progress_status[session_id]["verbose_output"] = output.getvalue()
            else:
                update_progress(session_id, 100, "Processing complete")
                progress_status[session_id]["status"] = "complete"
                progress_status[session_id]["result"] = result
                progress_status[session_id]["verbose_output"] = output.getvalue()
                
    except Exception as e:
        progress_status[session_id] = {
            "progress": 100, 
            "status": "error", 
            "message": f"Error: {str(e)}"
        }

def process_feedback_async(session_id, feedback_text, approved):
    """Process human feedback asynchronously"""
    try:
        progress_status[session_id]["status"] = "processing_feedback"
        update_progress(session_id, 20, "Processing your feedback...")
        
        if approved:
            update_progress(session_id, 100, "Plan approved and finalized!")
            progress_status[session_id]["status"] = "complete"
            progress_status[session_id]["approved"] = True
        else:
            update_progress(session_id, 50, "Revising plan based on feedback...")
            
            # Get the stored config
            config = progress_status[session_id].get("config")
            if config:
                with capture_stdout() as output:
                    # Continue after interrupt with feedback
                    result = chatbot.continue_after_interrupt(feedback_text, approved, config)
                    
                    update_progress(session_id, 80, "Generating revised plan...")
                    
                    # Extract revised plan from result
                    revised_plan = None
                    if result.get("messages"):
                        for message in reversed(result["messages"]):
                            if hasattr(message, 'name') and message.name == "generate_response_plan":
                                revised_plan = message.content
                                break
                    
                    progress_status[session_id]["revised_plan"] = format_response_plan(revised_plan) if revised_plan else revised_plan
                    progress_status[session_id]["feedback_result"] = result
                    progress_status[session_id]["feedback_verbose"] = output.getvalue()
                    
                update_progress(session_id, 100, "Revised plan ready!")
                progress_status[session_id]["status"] = "complete"
                progress_status[session_id]["approved"] = False
            else:
                # Fallback if no config available
                update_progress(session_id, 100, "Error: No configuration available")
                progress_status[session_id]["status"] = "error"
                progress_status[session_id]["message"] = "No configuration available for feedback processing"
            
    except Exception as e:
        progress_status[session_id] = {
            "progress": 100,
            "status": "error", 
            "message": f"Feedback processing error: {str(e)}"
        }

@app.route("/", methods=["GET", "POST"])
def index():
    # Get or create session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    session_id = session['session_id']
    
    # Initialize template variables
    waiting_feedback = False
    final_result = False
    response_plan = None
    observations = None
    verbose_output = None
    approved = False
    final_plan = None
    
    if request.method == "POST":
        # Check if this is initial input or feedback
        if 'user_input' in request.form:
            # Initial request
            user_input = request.form.get("user_input", "")
            if user_input:
                # Reset session state
                progress_status[session_id] = {"progress": 0, "status": "idle", "message": ""}
                
                # Start async processing
                threading.Thread(target=process_request_async, args=(session_id, user_input)).start()
                
                # Wait for initial processing or feedback requirement
                timeout = 120  # 2 minutes timeout
                start_time = time.time()
                
                while (progress_status[session_id]["status"] not in ["waiting_feedback", "complete", "error"] and 
                       (time.time() - start_time) < timeout):
                    time.sleep(0.5)
                
                if progress_status[session_id]["status"] == "waiting_feedback":
                    waiting_feedback = True
                    # Extract response plan from stored data
                    response_plan = progress_status[session_id].get("response_plan", "No plan found")
                    
                    observations = "AI agent has analyzed the incident and generated a response plan."
                    verbose_output = progress_status[session_id].get("verbose_output", "")
                    
        elif 'feedback_text' in request.form:
            # Human feedback
            feedback_text = request.form.get("feedback_text", "")
            approved = request.form.get("approved", "false").lower() == "true"
            
            # Start async feedback processing
            threading.Thread(target=process_feedback_async, args=(session_id, feedback_text, approved)).start()
            
            # Wait for feedback processing
            timeout = 60  # 1 minute timeout for feedback
            start_time = time.time()
            
            while (progress_status[session_id]["status"] not in ["complete", "error"] and 
                   (time.time() - start_time) < timeout):
                time.sleep(0.5)
            
            if progress_status[session_id]["status"] == "complete":
                final_result = True
                approved = progress_status[session_id].get("approved", False)
                
                # Get the final plan
                if approved:
                    # Use the original plan
                    final_plan = progress_status[session_id].get("response_plan", "No plan found")
                else:
                    # Use the revised plan
                    final_plan = progress_status[session_id].get("revised_plan", "No revised plan found")
                
                # Combine verbose outputs
                verbose_output = progress_status[session_id].get("verbose_output", "")
                if "feedback_verbose" in progress_status[session_id]:
                    verbose_output += "\n\n=== FEEDBACK PROCESSING ===\n\n"
                    verbose_output += progress_status[session_id]["feedback_verbose"]
                
                observations = f"Plan {'approved' if approved else 'revised'} based on human feedback."
    
    return render_template_string(
        HTML_TEMPLATE,
        session_id=session_id,
        waiting_feedback=waiting_feedback,
        final_result=final_result,
        response_plan=response_plan,
        observations=observations,
        verbose_output=verbose_output,
        approved=approved,
        final_plan=final_plan
    )

if __name__ == "__main__":
    print("🚀 Starting RPG2 Web UI...")
    print("🌐 Access the application at: http://127.0.0.1:8080/")
    print("📝 This UI supports human-in-the-loop response plan review")
    app.run(debug=True, host='127.0.0.1', port=8080)
