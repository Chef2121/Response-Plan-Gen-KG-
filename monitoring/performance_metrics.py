"""Performance monitoring and metrics collection."""

import time
import json
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class PerformanceMetric:
    """Single performance measurement."""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class PerformanceMonitor:
    """Monitor and track system performance metrics."""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.active_timers: Dict[str, float] = {}
    
    def start_timer(self, operation_name: str) -> str:
        """Start timing an operation."""
        timer_id = f"{operation_name}_{time.time()}"
        self.active_timers[timer_id] = time.time()
        return timer_id
    
    def end_timer(self, timer_id: str, metadata: Dict[str, Any] = None) -> float:
        """End timing and record the metric."""
        if timer_id not in self.active_timers:
            raise ValueError(f"Timer {timer_id} not found")
        
        start_time = self.active_timers.pop(timer_id)
        duration = time.time() - start_time
        
        operation_name = timer_id.split('_')[0]
        self.record_metric(
            name=f"{operation_name}_duration",
            value=duration,
            unit="seconds",
            metadata=metadata or {}
        )
        
        return duration
    
    def record_metric(self, name: str, value: float, unit: str, metadata: Dict[str, Any] = None):
        """Record a performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            metadata=metadata or {}
        )
        self.metrics.append(metric)
    
    def get_metrics_summary(self, operation_name: str = None) -> Dict[str, Any]:
        """Get summary statistics for metrics."""
        if operation_name:
            filtered_metrics = [m for m in self.metrics if operation_name in m.name]
        else:
            filtered_metrics = self.metrics
        
        if not filtered_metrics:
            return {"error": "No metrics found"}
        
        values = [m.value for m in filtered_metrics]
        
        return {
            "operation": operation_name or "all",
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "total": sum(values),
            "unit": filtered_metrics[0].unit if filtered_metrics else "unknown"
        }
    
    def get_recent_metrics(self, hours: int = 1) -> List[PerformanceMetric]:
        """Get metrics from the last N hours."""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        return [
            m for m in self.metrics 
            if m.timestamp.timestamp() > cutoff_time
        ]
    
    def export_metrics(self, filename: str = None) -> str:
        """Export metrics to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_metrics_{timestamp}.json"
        
        metrics_data = []
        for metric in self.metrics:
            metrics_data.append({
                "name": metric.name,
                "value": metric.value,
                "unit": metric.unit,
                "timestamp": metric.timestamp.isoformat(),
                "metadata": metric.metadata
            })
        
        try:
            with open(filename, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            return f"Metrics exported to {filename}"
        except Exception as e:
            return f"Export failed: {e}"
    
    def clear_metrics(self):
        """Clear all stored metrics."""
        self.metrics.clear()
    
    def print_summary(self):
        """Print a summary of all metrics."""
        if not self.metrics:
            print("📊 No performance metrics recorded")
            return
        
        print("📊 PERFORMANCE SUMMARY")
        print("=" * 50)
        
        # Group metrics by operation
        operations = set(m.name.split('_')[0] for m in self.metrics)
        
        for operation in sorted(operations):
            summary = self.get_metrics_summary(operation)
            if "error" not in summary:
                print(f"\n🔧 {operation.upper()}")
                print(f"  Count: {summary['count']}")
                print(f"  Mean: {summary['mean']:.3f} {summary['unit']}")
                print(f"  Min/Max: {summary['min']:.3f} / {summary['max']:.3f} {summary['unit']}")
                if summary['count'] > 1:
                    print(f"  Std Dev: {summary['std_dev']:.3f} {summary['unit']}")

class SystemMonitor:
    """Monitor overall system health and performance."""
    
    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
        self.system_stats = {}
        self.alerts = []
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # Check database connectivity
        try:
            from config.database import get_neo4j_driver
            driver = get_neo4j_driver()
            with driver.session() as session:
                result = session.run("RETURN 1")
                record = result.single()
                health_status["checks"]["database"] = "healthy" if record else "unhealthy"
        except Exception as e:
            health_status["checks"]["database"] = f"unhealthy: {e}"
            health_status["status"] = "degraded"
        
        # Check LLM availability
        try:
            from config.llm import get_llm
            llm = get_llm()
            health_status["checks"]["llm"] = "healthy"
        except Exception as e:
            health_status["checks"]["llm"] = f"unhealthy: {e}"
            health_status["status"] = "degraded"
        
        # Check recent performance
        recent_metrics = self.performance_monitor.get_recent_metrics(1)
        if recent_metrics:
            avg_duration = statistics.mean(m.value for m in recent_metrics if "duration" in m.name)
            if avg_duration > 30:  # Alert if average operation takes > 30 seconds
                health_status["checks"]["performance"] = f"slow: {avg_duration:.2f}s average"
                health_status["status"] = "degraded"
            else:
                health_status["checks"]["performance"] = f"good: {avg_duration:.2f}s average"
        else:
            health_status["checks"]["performance"] = "no recent data"
        
        return health_status

# Global monitors
performance_monitor = PerformanceMonitor()
system_monitor = SystemMonitor()
