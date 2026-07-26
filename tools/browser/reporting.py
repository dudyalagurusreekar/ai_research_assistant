import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

class ExecutionReport:
    """
    Standardized execution report capturing metrics, artifacts, timing breakdowns,
    and outcomes for a browser execution task.
    """
    def __init__(self, task_id: str, goal: str) -> None:
        self.task_id = task_id
        self.goal = goal
        self.success = False
        self.final_output: Optional[str] = None
        self.steps_taken = 0
        self.total_duration_ms = 0.0
        
        # Timing breakdowns
        self.dom_simplify_time_ms = 0.0
        self.llm_inference_time_ms = 0.0
        self.action_execution_time_ms = 0.0
        
        # Token metrics
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        
        # Artifacts
        self.screenshots: List[str] = []
        self.extracted_artifacts: List[str] = []
        
        # Diagnostics
        self.errors: List[str] = []
        self.verification_status: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the report to a dictionary representation."""
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "success": self.success,
            "final_output": self.final_output,
            "steps_taken": self.steps_taken,
            "metrics": {
                "total_duration_ms": round(self.total_duration_ms, 2),
                "timing_breakdown": {
                    "dom_simplify_time_ms": round(self.dom_simplify_time_ms, 2),
                    "llm_inference_time_ms": round(self.llm_inference_time_ms, 2),
                    "action_execution_time_ms": round(self.action_execution_time_ms, 2),
                },
                "tokens": {
                    "total_tokens": self.total_tokens,
                    "prompt_tokens": self.prompt_tokens,
                    "completion_tokens": self.completion_tokens,
                }
            },
            "artifacts": {
                "screenshots": self.screenshots,
                "extracted_artifacts": self.extracted_artifacts,
            },
            "verification_status": self.verification_status,
            "errors": self.errors
        }

    def save_to_file(self, output_path: str) -> None:
        """Saves the JSON report to the specified path."""
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)


class ReportingEngine:
    """
    Orchestrates execution telemetry gathering and writes standardized JSON report outputs.
    """
    @staticmethod
    def generate_report(task_id: str, goal: str, planner_state: Any, start_time: float, final_output: Optional[str] = None) -> ExecutionReport:
        """Constructs an ExecutionReport from the planner's state and timing.

        Args:
            task_id (str): Unique identifier.
            goal (str): Natural language goal string.
            planner_state (PlannerState): State tracking model.
            start_time (float): Loop start Unix timestamp.
            final_output (Optional[str]): Answer value returned.

        Returns:
            ExecutionReport: Telemetry report instance.
        """
        report = ExecutionReport(task_id, goal)
        report.success = getattr(planner_state, "success", False)
        report.final_output = final_output
        
        history = getattr(planner_state, "history", [])
        report.steps_taken = len(history)
        report.total_duration_ms = (time.time() - start_time) * 1000.0
        
        # Calculate execution timings
        for step in history:
            report.action_execution_time_ms += step.get("duration_ms", 0.0)
            report.dom_simplify_time_ms += step.get("dom_simplify_time_ms", 0.0)
            report.llm_inference_time_ms += step.get("llm_inference_time_ms", 0.0)
        
        report.total_tokens = getattr(planner_state, "total_tokens_used", 0)
        
        # Capture screenshots & artifacts
        report.screenshots = list(getattr(planner_state, "screenshots", []))
        report.extracted_artifacts = list(getattr(planner_state, "artifacts", []))
        report.errors = list(getattr(planner_state, "errors", []))
        
        # Compile verification metrics
        report.verification_status = {
            "steps_completed_successfully": sum(1 for s in history if s.get("success", False)),
            "navigation_occurred": any(s.get("command") == "open_url" and s.get("success") for s in history),
        }
        
        return report
