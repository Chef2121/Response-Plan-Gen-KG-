from flask import Flask, request, render_template_string, jsonify
from rpg import SessionAwareChatBot
import sys
from io import StringIO
import contextlib
import threading
import time

app = Flask(__name__)
chatbot = SessionAwareChatBot()

# Global variable to track progress
progress_status = {"progress": 0, "status": "idle", "message": ""}

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
                    
                    progressBar.style.width = data.progress + '%';
                    progressText.textContent = data.progress + '%';
                    progressMessage.textContent = data.message;
                    
                    if (data.status === 'complete' || data.status === 'error') {
                        clearInterval(progressInterval);
                        document.getElementById('progress-container').style.display = 'none';
                        document.getElementById('submit-btn').disabled = false;
                        if (data.status === 'complete') {
                            location.reload(); // Reload to show results
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
            progressInterval = setInterval(updateProgress, 500);
            
            // Submit the form
            document.getElementById('main-form').submit();
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
    </script>
</head>
<body>
    <h1>Response Plan Generator</h1>
    <form id="main-form" method="post">
        <label>Enter your question or incident details:</label>
        <br><br>
        <textarea name="user_input" rows="4" cols="60"></textarea>
        <br><br>
        <button type="button" id="submit-btn" onclick="submitForm()">Generate Plan</button>
    </form>
    
    <div id="progress-container" class="progress-container">
        <div class="progress-bar">
            <div id="progress-fill" class="progress-fill"></div>
            <div id="progress-text" class="progress-text">0%</div>
        </div>
        <div id="progress-message" class="progress-message">Initializing...</div>
    </div>
    
    {% if response %}
    <hr>
    <h2>Response:</h2>
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

def process_request_async(user_input):
    global progress_status
    try:
        progress_status = {"progress": 0, "status": "processing", "message": "Initializing chatbot..."}
        
        update_progress(10, "Starting agent processing...")
        
        # Capture the verbose output and get intermediate steps
        with capture_stdout() as output:
            update_progress(99, "Invoking agent...")
            
            # Get the full agent response with intermediate steps
            full_response = chatbot.agent.invoke({
                "input": user_input,
                "chat_history": chatbot.chat_history
            })
            
            update_progress(50, "Processing response...")
            
            response = full_response.get("output", "")
            
            update_progress(70, "Extracting observations...")
            
            # Extract observations from intermediate steps
            obs_html = ""
            plan_html = ""
            
            if "intermediate_steps" in full_response:
                for i, (action, observation) in enumerate(full_response["intermediate_steps"]):
                    obs_html += f'<div class="observation-step">'
                    obs_html += f'<strong>Step {i+1} - Tool:</strong> {action.tool}<br>'
                    obs_html += f'<strong>Input:</strong> {action.tool_input}<br>'
                    obs_html += f'<strong>Observation:</strong> {observation}'
                    obs_html += '</div>'
                    
                    if getattr(action, "tool", "") == "GenerateSmartResponsePlan":
                        plan_html += f'Observation:{observation}'
            
            update_progress(90, "Updating chat history...")
            
            # Update chat history
            chatbot.chat_history.extend([
                ("human", user_input),
                ("ai", response)
            ])
            
            update_progress(100, "Complete!")
            
            # Store results globally for the main thread to access
            progress_status["results"] = {
                "response": response,
                "observations": obs_html,
                "plan": plan_html if plan_html else None,
                "verbose_output": output.getvalue()
            }
            progress_status["status"] = "complete"
            
    except Exception as e:
        progress_status = {"progress": 100, "status": "error", "message": f"Error: {str(e)}"}

@app.route("/", methods=["GET", "POST"])
def index():
    global progress_status
    response = None
    verbose_output = None
    observations = None
    plan = None
    
    if request.method == "POST":
        user_input = request.form.get("user_input", "")
        if user_input:
            # Reset progress
            progress_status = {"progress": 0, "status": "idle", "message": ""}
            
            # Start async processing
            threading.Thread(target=process_request_async, args=(user_input,)).start()
            
            # Wait for completion (with timeout)
            timeout = 60  # 60 seconds timeout
            start_time = time.time()
            
            while progress_status["status"] not in ["complete", "error"] and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if progress_status["status"] == "complete" and "results" in progress_status:
                results = progress_status["results"]
                response = results["response"]
                observations = results["observations"]
                plan = results["plan"]
                verbose_output = results["verbose_output"]
    
    return render_template_string(HTML_TEMPLATE, response=plan, verbose_output=verbose_output, observations=observations)

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=8080)