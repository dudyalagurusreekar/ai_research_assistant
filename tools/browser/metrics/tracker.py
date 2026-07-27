"""Browser Metrics Tracker recording telemetry and error metrics."""

import time
from typing import Any, Dict, List, Optional
from infrastructure.monitoring.monitor import InfrastructureMonitor


class BrowserMetricsTracker:
    """Tracks latency, action statistics, DOM processing times, and browser errors."""

    def __init__(self, monitor: Optional[InfrastructureMonitor] = None) -> None:
        self.monitor = monitor or InfrastructureMonitor()
        self.action_counts: Dict[str, int] = {}
        self.action_latencies_ms: Dict[str, List[float]] = {}
        self.errors: List[Dict[str, Any]] = []

    def record_action(self, action_name: str, duration_ms: float, success: bool = True) -> None:
        """Record browser action latency and execution status."""
        self.action_counts[action_name] = self.action_counts.get(action_name, 0) + 1
        if action_name not in self.action_latencies_ms:
            self.action_latencies_ms[action_name] = []
        self.action_latencies_ms[action_name].append(duration_ms)

        self.monitor.record_tool_execution("browser_tool", duration_ms, success)

    def record_error(self, action: str, error_msg: str) -> None:
        """Record a browser automation error."""
        self.errors.append({"timestamp": time.time(), "action": action, "error": error_msg})
        self.monitor.record_error("browser_error", error_msg, {"action": action})

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Compile a summary dictionary of browser metrics."""
        avg_latencies = {
            act: sum(durs) / max(1, len(durs)) for act, durs in self.action_latencies_ms.items()
        }
        return {
            "total_actions": sum(self.action_counts.values()),
            "action_breakdown": self.action_counts,
            "average_latencies_ms": avg_latencies,
            "error_count": len(self.errors),
        }
