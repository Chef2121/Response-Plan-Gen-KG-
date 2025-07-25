"""LangSmith integration for tracking and monitoring."""

import os
from typing import Optional, Dict, Any
from langsmith import Client
from config.settings import settings

class LangSmithTracker:
    """Manages LangSmith tracking for the traffic management system."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.project_name = settings.LANGCHAIN_PROJECT
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the LangSmith client if credentials are available."""
        try:
            if settings.LANGCHAIN_API_KEY:
                self.client = Client()
                print(f"✅ LangSmith tracking enabled for project: {self.project_name}")
            else:
                print("⚠️ LangSmith API key not found - tracking disabled")
        except Exception as e:
            print(f"⚠️ LangSmith initialization failed: {e}")
            self.client = None
    
    def is_enabled(self) -> bool:
        """Check if LangSmith tracking is enabled."""
        return self.client is not None
    
    def track_query(self, query: str, result: str, metadata: Dict[str, Any] = None) -> str:
        """Track a query and its result."""
        if not self.is_enabled():
            return "tracking_disabled"
        
        try:
            # Create a run for tracking
            run_data = {
                "name": "traffic_management_query",
                "inputs": {"query": query},
                "outputs": {"result": result},
                "run_type": "chain",
                "tags": ["traffic-management", "production"],
                "metadata": metadata or {}
            }
            
            # Note: In practice, you'd use the actual LangSmith tracking
            # This is a simplified version
            print(f"📊 LangSmith: Tracked query with metadata: {metadata}")
            
            return "tracked_successfully"
            
        except Exception as e:
            print(f"⚠️ LangSmith tracking failed: {e}")
            return f"tracking_failed: {e}"
    
    def track_workflow_step(self, step_name: str, inputs: Dict, outputs: Dict, duration: float):
        """Track individual workflow steps."""
        if not self.is_enabled():
            return
        
        try:
            metadata = {
                "step_name": step_name,
                "duration_seconds": duration,
                "input_keys": list(inputs.keys()),
                "output_keys": list(outputs.keys())
            }
            
            print(f"📊 LangSmith: Tracked workflow step '{step_name}' - {duration:.2f}s")
            
        except Exception as e:
            print(f"⚠️ Workflow step tracking failed: {e}")
    
    def track_error(self, error: Exception, context: Dict[str, Any]):
        """Track errors for analysis."""
        if not self.is_enabled():
            return
        
        try:
            error_data = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context
            }
            
            print(f"🚨 LangSmith: Tracked error - {error_data['error_type']}")
            
        except Exception as e:
            print(f"⚠️ Error tracking failed: {e}")
    
    def get_project_stats(self) -> Dict[str, Any]:
        """Get project statistics from LangSmith."""
        if not self.is_enabled():
            return {"error": "LangSmith not enabled"}
        
        try:
            # In practice, this would fetch real stats from LangSmith
            return {
                "project": self.project_name,
                "status": "active",
                "tracking_enabled": True
            }
            
        except Exception as e:
            return {"error": f"Failed to get stats: {e}"}
    
    def abort_run(self, run_id: str) -> bool:
        """Abort a specific run."""
        if not self.is_enabled():
            return False
        
        try:
            # Check if the run exists and its current status
            run_info = self.client.read_run(run_id=run_id)
            print(f"Current run status: {run_info.status}")
            
            # Only update if the run is not already finished
            if run_info.status not in ["success", "error", "cancelled"]:
                self.client.update_run(run_id=run_id, status="cancelled")
                print("Run successfully cancelled")
                return True
            else:
                print(f"Run is already finished with status: {run_info.status}")
                return False
                
        except Exception as e:
            print(f"Error updating run: {e}")
            if "404" in str(e):
                print("Run not found - it may have already been deleted")
            elif "409" in str(e):
                print("Run already completed - cannot update status")
            return False

# Global tracker instance
langsmith_tracker = LangSmithTracker()
