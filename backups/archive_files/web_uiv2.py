from flask import Flask, request, render_template_string, jsonify, session
from rpg2 import RoadNetworkChatBot
import sys
from io import StringIO
import contextlib
import threading
import time
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key
chatbot = RoadNetworkChatBot()

# Global variable to track progress and pending approvals
progress_status = {"progress": 0, "status": "idle", "message": ""}
pending_approvals = {}  # Store pending approval requests

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Response Plan Web UI</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        textarea { width: 100%; max-width: 600px; }
        .response { 
            background-color: #f5f5f5; 
            padding: 15px; 
            border-radius: 5px; 
            white-space: pre-wrap; 
            word-wrap: break-word;
            max-width: 800px;
            overflow-x: auto;
            margin-bottom: 20px;
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
            max-width: 800px;
            overflow-x: auto;
            font-family: monospace;
            font-size: 12px;
            border-left: 4px solid #007acc;
        }
        .toggle-btn {
            background-color: #007acc;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
            cursor: pointer;
            margin-bottom: 10px;
        }
        .progress-container {
            width: 100%;
            max-width: 600px;
            margin: 20px 0;
            display: none;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            position: relative;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #007acc, #4fc3f7);
            border-radius: 10px;
            transition: width 0.3s ease;
            width: 0%;
        }
        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 12px;
            font-weight: bold;
            color: #333;
        }
        .progress-message {
            margin-top: 10px;
            font-size: 14px;
            color: #666;
        }
        #submit-btn {
            background-color: #007acc;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        #submit-btn:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .review-section {
            background-color: #f8f9fa;
            border: 2px solid #007acc;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            max-width: 800px;
        }
        .plan-display {
            background-color: #ffffff;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            white-space: pre-wrap;
            word-wrap: break-word;
            border-left: 4px solid #28a745;
            max-height: 400px;
            overflow-y: auto;
        }
        .chat-container {
            margin-top: 20px;
        }
        .chat-input {
            width: 100%;
            max-width: 600px;
            min-height: 80px;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            resize: vertical;
            margin-bottom: 15px;
        }
        .chat-input:focus {
            outline: none;
            border-color: #007acc;
            box-shadow: 0 0 5px rgba(0, 122, 204, 0.3);
        }
        .chat-actions {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .approve-btn {
            background-color: #28a745;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
        }
        .approve-btn:hover {
            background-color: #218838;
        }
        .feedback-btn {
            background-color: #ffc107;
            color: #212529;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
        }
        .feedback-btn:hover {
            background-color: #e0a800;
        }
        .quick-feedback {
            margin-top: 10px;
        }
        .quick-feedback-btn {
            background-color: #6c757d;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
            margin-right: 5px;
            margin-bottom: 5px;
        }
        .quick-feedback-btn:hover {
            background-color: #5a6268;
        }
        .waiting-approval {
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
            color: #0c5460;
        }
        .help-text {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
            font-style: italic;
        }
    </style>
    <script>
        let progressInterval;
        
        function updateProgress() {
            fetch('/progress')
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
                    
                    if (data.status === 'complete' || data.status === 'error') {
                        clearInterval(progressInterval);
                        if (document.getElementById('progress-container')) {
                            document.getElementById('progress-container').style.display = 'none';
                        }
                        if (document.getElementById('submit-btn')) {
                            document.getElementById('submit-btn').disabled = false;
                        }
                        if (data.status === 'complete') {
                            location.reload();
                        }
                    } else if (data.status === 'waiting_approval') {
                        clearInterval(progressInterval);
                        if (document.getElementById('progress-container')) {
                            document.getElementById('progress-container').style.display = 'none';
                        }
                        if (document.getElementById('submit-btn')) {
                            document.getElementById('submit-btn').disabled = false;
                        }
                        location.reload();
                    }
                });
        }
        
        function submitForm() {
            const submitBtn = document.getElementById('submit-btn');
            const progressContainer = document.getElementById('progress-container');
            
            if (submitBtn && progressContainer) {
                submitBtn.disabled = true;
                progressContainer.style.display = 'block';
                
                progressInterval = setInterval(updateProgress, 500);
                document.getElementById('main-form').submit();
            }
        }
        
        function approvePlan() {
            const form = document.getElementById('feedback-form');
            const feedbackInput = document.getElementById('feedback-input');
            
            feedbackInput.value = 'approve';
            form.submit();
        }
        
        function submitFeedback() {
            const feedbackInput = document.getElementById('feedback-input');
            const feedbackText = feedbackInput.value.trim();
            
            if (!feedbackText) {
                alert('Please enter your feedback or click "Approve Plan" to approve.');
                return;
            }
            
            if (feedbackText.toLowerCase() === 'approve') {
                if (confirm('Are you sure you want to approve this plan?')) {
                    document.getElementById('feedback-form').submit();
                }
            } else {
                document.getElementById('feedback-form').submit();
            }
        }
        
        function addQuickFeedback(text) {
            const feedbackInput = document.getElementById('feedback-input');
            const currentText = feedbackInput.value.trim();
            
            if (currentText) {
                feedbackInput.value = currentText + '. ' + text;
            } else {
                feedbackInput.value = text;
            }
            
            feedbackInput.focus();
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
        
        // Auto-resize textarea
        document.addEventListener('DOMContentLoaded', function() {
            const textarea = document.getElementById('feedback-input');
            if (textarea) {
                textarea.addEventListener('input', function() {
                    this.style.height = 'auto';
                    this.style.height = (this.scrollHeight) + 'px';
                });
            }
        });
    </script>
</head>
<body>
    <h1>Response Plan Generator</h1>
    
    {% if not pending_approval %}
    <form id="main-form" method="post">
        <label>Enter your question or incident details:</label>
        <br><br>
        <textarea name="user_input" rows="4" cols="60" placeholder="Describe the traffic incident or situation...">{{ user_input or '' }}</textarea>
        <br><br>
        <button type="button" id="submit-btn" onclick="submitForm()">Generate Plan</button>
    </form>
    {% endif %}
    
    <div id="progress-container" class="progress-container">
        <div class="progress-bar">
            <div id="progress-fill" class="progress-fill"></div>
            <div id="progress-text" class="progress-text">0%</div>
        </div>
        <div id="progress-message" class="progress-message">Initializing...</div>
    </div>
    
    {% if pending_approval %}
    <div class="review-section">
        <h2>🔍 Response Plan Review</h2>
        <p><strong>Please review the generated response plan below:</strong></p>
        
        <div class="plan-display">{{ pending_approval.plan }}</div>
        
        <div class="chat-container">
            <form id="feedback-form" method="post" action="/approve">
                <input type="hidden" name="session_id" value="{{ pending_approval.session_id }}">
                
                <label for="feedback-input"><strong>Your Feedback:</strong></label>
                <div class="help-text">Type "approve" to accept the plan, or provide specific feedback for improvements</div>
                
                <textarea id="feedback-input" name="feedback" class="chat-input" 
                          placeholder="Type 'approve' to accept the plan, or provide specific feedback such as:
- Change the message timing
- Use different VMS locations  
- Modify the wording
- Add more emergency services
- Adjust the priority level
etc."></textarea>
                
                <div class="chat-actions">
                    <button type="button" class="approve-btn" onclick="approvePlan()">
                        ✅ Approve Plan
                    </button>
                    <button type="button" class="feedback-btn" onclick="submitFeedback()">
                        💬 Send Feedback
                    </button>
                </div>
                
                <div class="quick-feedback">
                    <strong>Quick feedback options:</strong><br>
                    <button type="button" class="quick-feedback-btn" onclick="addQuickFeedback('Make messages more urgent')">More Urgent</button>
                    <button type="button" class="quick-feedback-btn" onclick="addQuickFeedback('Use clearer language')">Clearer Language</button>
                    <button type="button" class="quick-feedback-btn" onclick="addQuickFeedback('Add more VMS signs')">More VMS</button>
                    <button type="button" class="quick-feedback-btn" onclick="addQuickFeedback('Reduce message duration')">Shorter Duration</button>
                    <button type="button" class="quick-feedback-btn" onclick="addQuickFeedback('Include alternative routes')">Alt Routes</button>
                    <button type="button" class="quick-feedback-btn" onclick="addQuickFeedback('Notify more emergency services')">More Services</button>
                </div>
            </form>
        </div>
    </div>
    {% endif %}
    
    {% if waiting_for_processing %}
    <div class="waiting-approval">
        <h3>⏳ Processing your feedback...</h3>
        <p>The system is incorporating your feedback and generating an improved response plan.</p>
        <p><em>This page will automatically refresh when the new plan is ready for review.</em></p>
        <script>
            setTimeout(function() {
                location.reload();
            }, 3000);
        </script>
    </div>
    {% endif %}
    
    {% if response %}
    <hr>
    <h2>✅ Final Approved Response Plan:</h2>
    <div class="response">{{ response }}</div>
    
    {% if observations %}
    <button id="toggle-obs-btn" class="toggle-btn" onclick="toggleObservations()">Show Observations</button>
    <div id="observations-output" class="observations" style="display: none;">
        <h3>Agent Observations:</h3>
        {{ observations | safe }}
    </div>
    {% endif %}
    
    {% if verbose_output %}
    <button id="toggle-btn" class="toggle-btn" onclick="toggleVerbose()">Show Debug Info</button>
    <div id="verbose-output" class="verbose" style="display: none;">
        <h3>Debug Information:</h3>
        {{ verbose_output }}
    </div>
    {% endif %}
    {% endif %}
</body>
</html>
"""

def update_progress(progress, message):
    global progress_status
    progress_status["progress"] = progress
    progress_status["message"] = message

@contextlib.contextmanager
def capture_stdout():
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    try:
        yield captured_output
    finally:
        sys.stdout = old_stdout

@app.route("/progress")
def get_progress():
    return jsonify(progress_status)

def process_request_async(user_input, session_id, feedback=None):
    global progress_status, pending_approvals
    try:
        progress_status = {"progress": 0, "status": "processing", "message": "Initializing chatbot..."}
        
        update_progress(10, "Starting agent processing...")
        
        # Import the message classes
        from langchain_core.messages import HumanMessage
        
        # Capture the verbose output
        with capture_stdout() as output:
            update_progress(20, "Processing with LangGraph workflow...")
            
            # Use the original workflow from rpg2
            from rpg2 import app as rpg_app
            
            update_progress(30, "Invoking workflow...")
            
            # Create initial state with proper LangChain message format
            messages = [HumanMessage(content=user_input)]
            
            # If this is a revision, add the feedback
            if feedback:
                messages.append(HumanMessage(content=f"Please revise the plan based on this feedback: {feedback}"))
            
            initial_state = {
                "messages": messages,
                "tool_calls": [],
                "user_feedback": feedback or "",
                "final_approved": False,
                "revision_count": 0,
                "needs_revision": bool(feedback),
                "current_plan": ""
            }
            
            config = {
                "configurable": {"thread_id": session_id},
                "run_name": f"web_ui_query_{session_id}",
                "tags": ["web-ui", "traffic-management"],
                "metadata": {"source": "web_interface"}
            }
            
            # Monkey patch the human_feedback function to work with web UI
            import rpg2
            original_human_feedback = getattr(rpg2, 'human_feedback', None)
            
            def web_human_feedback(state):
                """Custom human feedback function for web UI"""
                # Extract the current plan from the state
                plan = "No plan found"
                
                # Look for the plan in messages - check for generate_response_plan tool results
                for message in reversed(state.get("messages", [])):
                    if hasattr(message, 'name') and message.name == "generate_response_plan":
                        plan = message.content
                        break
                    elif hasattr(message, 'content') and message.content:
                        # Check if this message contains plan-like content
                        content = str(message.content)
                        if any(keyword in content.lower() for keyword in ["plan_type", "traffic_management_actions", "priority", "estimated_duration"]):
                            plan = content
                            break
                
                # If still no plan found, try to extract from tool calls
                if plan == "No plan found":
                    for message in reversed(state.get("messages", [])):
                        if hasattr(message, 'tool_calls') and message.tool_calls:
                            for tool_call in message.tool_calls:
                                if tool_call.get("name") == "generate_response_plan":
                                    plan = f"Tool called: {tool_call.get('args', {})}"
                                    break
                
                print(f"🔍 Web UI: Extracted plan for approval: {plan}")
                
                # Store the plan for web approval
                pending_approvals[session_id] = {
                    "plan": plan,
                    "state": state.copy(),
                    "session_id": session_id
                }
                
                progress_status["status"] = "waiting_approval"
                progress_status["message"] = "Plan ready for review"
                progress_status["progress"] = 100
                
                print(f"🔍 Web UI: Plan stored for session {session_id}, waiting for approval")
                
                # Return the current state to pause execution
                return state
            
            # Replace the human feedback function
            rpg2.human_feedback = web_human_feedback
            
            try:
                # Run the workflow
                update_progress(40, "Running LangGraph workflow...")
                
                # Stream through the workflow to handle the approval process
                current_state = initial_state
                step_count = 0
                max_steps = 20  # Prevent infinite loops
                
                for chunk in rpg_app.stream(initial_state, config):
                    step_count += 1
                    if step_count > max_steps:
                        break
                        
                    print(f"🔍 Web UI: Processing chunk {step_count}: {list(chunk.keys())}")
                    
                    # Update progress
                    progress_percent = min(40 + (step_count * 5), 90)
                    update_progress(progress_percent, f"Processing step {step_count}...")
                    
                    # Check if we hit the human feedback node
                    if progress_status["status"] == "waiting_approval":
                        print("🔍 Web UI: Workflow paused for approval")
                        return  # Exit and wait for web approval
                    
                    # Update current state with the latest chunk
                    for node_name, node_output in chunk.items():
                        if isinstance(node_output, dict):
                            current_state.update(node_output)
                
                # If we get here, the workflow completed without approval
                update_progress(80, "Processing workflow results...")
                
                # Extract response from the final state
                response = "No response generated"
                observations = ""
                plan_content = ""
                
                if current_state and "messages" in current_state:
                    # Look for the final response
                    for message in reversed(current_state["messages"]):
                        if hasattr(message, 'content') and message.content:
                            if hasattr(message, 'name') and message.name == "generate_response_plan":
                                plan_content = message.content
                                response = plan_content
                                break
                            elif not hasattr(message, 'name'):
                                # This is likely the final AI response
                                response = message.content
                                break
                    
                    # Extract observations from tool calls and messages
                    obs_html = ""
                    step_count = 1
                    
                    for message in current_state["messages"]:
                        # Handle tool calls
                        if hasattr(message, 'tool_calls') and message.tool_calls:
                            for tool_call in message.tool_calls:
                                obs_html += f'<div class="observation-step">'
                                obs_html += f'<strong>Step {step_count} - Tool:</strong> {tool_call.get("name", "Unknown")}<br>'
                                args = tool_call.get("args", {})
                                args_str = str(args)[:200] + "..." if len(str(args)) > 200 else str(args)
                                obs_html += f'<strong>Input:</strong> {args_str}<br>'
                                obs_html += '</div>'
                                step_count += 1
                        
                        # Handle tool responses
                        elif hasattr(message, 'name') and hasattr(message, 'content'):
                            obs_html += f'<div class="observation-step">'
                            obs_html += f'<strong>Tool Response ({message.name}):</strong><br>'
                            content_preview = str(message.content)[:500] + "..." if len(str(message.content)) > 500 else str(message.content)
                            obs_html += f'{content_preview}'
                            obs_html += '</div>'
                    
                    observations = obs_html if obs_html else "No tool interactions recorded"
                
                update_progress(90, "Finalizing response...")
                
                # Store results
                progress_status["results"] = {
                    "response": response,
                    "observations": observations,
                    "plan": plan_content,
                    "verbose_output": output.getvalue()
                }
                progress_status["status"] = "complete"
                progress_status["progress"] = 100
                
            finally:
                # Restore original function
                if original_human_feedback:
                    rpg2.human_feedback = original_human_feedback
            
    except Exception as e:
        progress_status = {"progress": 100, "status": "error", "message": f"Error: {str(e)}"}
        print(f"Error in process_request_async: {e}")
        import traceback
        traceback.print_exc()

@app.route("/approve", methods=["POST"])
def handle_approval():
    global pending_approvals, progress_status
    
    session_id = request.form.get("session_id")
    feedback = request.form.get("feedback", "").strip()
    
    if not feedback:
        # If no feedback provided, show error and return to review
        return render_template_string(HTML_TEMPLATE, 
                                    pending_approval=pending_approvals.get(session_id),
                                    error="Please provide feedback or type 'approve' to accept the plan.")
    
    if session_id in pending_approvals:
        approval_data = pending_approvals[session_id]
        
        # Check if user approved the plan
        if feedback.lower() == "approve":
            # Mark as approved and set final results
            progress_status["results"] = {
                "response": approval_data["plan"],
                "observations": "Plan approved by user",
                "plan": approval_data["plan"],
                "verbose_output": "Plan approved via web interface"
            }
            progress_status["status"] = "complete"
            del pending_approvals[session_id]
            
        else:
            # User provided feedback for revision
            del pending_approvals[session_id]
            user_input = session.get('user_input', '')
            session['waiting_for_processing'] = True
            
            # Reset progress for revision
            progress_status = {"progress": 0, "status": "processing", "message": "Processing feedback..."}
            
            # Start async processing with feedback
            threading.Thread(target=process_request_async, args=(user_input, session_id, feedback)).start()
            
            return render_template_string(HTML_TEMPLATE, 
                                        waiting_for_processing=True,
                                        user_input=user_input)
    
    return index()

@app.route("/", methods=["GET", "POST"])
def index():
    global progress_status, pending_approvals
    response = None
    verbose_output = None
    observations = None
    plan = None
    pending_approval = None
    waiting_for_processing = False
    
    # Check if we have a pending approval for this session
    session_id = session.get('session_id')
    if session_id and session_id in pending_approvals:
        pending_approval = pending_approvals[session_id]
    
    # Check if we're waiting for processing
    if session.get('waiting_for_processing'):
        waiting_for_processing = True
        session.pop('waiting_for_processing', None)
    
    if request.method == "POST":
        user_input = request.form.get("user_input", "")
        if user_input:
            # Create new session
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
            session['user_input'] = user_input
            
            # Reset progress
            progress_status = {"progress": 0, "status": "idle", "message": ""}
            
            # Start async processing
            threading.Thread(target=process_request_async, args=(user_input, session_id)).start()
            
            # Wait for completion or approval request
            timeout = 9999999
            start_time = time.time()
            
            while (progress_status["status"] not in ["complete", "error", "waiting_approval"] and 
                   (time.time() - start_time) < timeout):
                time.sleep(0.1)
            
            if progress_status["status"] == "waiting_approval":
                pending_approval = pending_approvals.get(session_id)
            elif progress_status["status"] == "complete" and "results" in progress_status:
                results = progress_status["results"]
                response = results["response"]
                observations = results["observations"]
                plan = results["plan"]
                verbose_output = results["verbose_output"]
            elif progress_status["status"] == "error":
                response = f"Error: {progress_status['message']}"
            else:
                response = "Request timed out. Please try again."
    
    return render_template_string(HTML_TEMPLATE, 
                                response=response, 
                                verbose_output=verbose_output, 
                                observations=observations,
                                pending_approval=pending_approval,
                                waiting_for_processing=waiting_for_processing,
                                user_input=session.get('user_input', ''))

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=8080)