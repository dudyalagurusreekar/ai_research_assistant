"""Execution State Tracker for the AI Browser Planner.

Maintains step history, visited URLs, action execution details, and performance metrics.
"""

import time
from typing import List, Dict, Any, Optional


class StepExecution:
    """Detailed log record of a single planned browser action step."""

    def __init__(
        self,
        step_number: int,
        thought: str,
        command: str,
        selector: Optional[str],
        text: Optional[str],
        result_message: str,
        success: bool,
        duration_ms: float,
        dom_simplify_time_ms: float = 0.0,
        llm_inference_time_ms: float = 0.0,
    ) -> None:
        self.step_number = step_number
        self.thought = thought
        self.command = command
        self.selector = selector
        self.text = text
        self.result_message = result_message
        self.success = success
        self.duration_ms = duration_ms
        self.dom_simplify_time_ms = dom_simplify_time_ms
        self.llm_inference_time_ms = llm_inference_time_ms
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize step execution record to dictionary."""
        return {
            "step": self.step_number,
            "thought": self.thought,
            "command": self.command,
            "selector": self.selector,
            "text": self.text,
            "result": self.result_message,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "dom_simplify_time_ms": self.dom_simplify_time_ms,
            "llm_inference_time_ms": self.llm_inference_time_ms,
            "timestamp": self.timestamp,
        }


class PlannerState:
    """Central state container for tracking current planning status and step history."""

    def __init__(self, goal: str) -> None:
        self.goal = goal
        self.history: List[StepExecution] = []
        self.current_step = 1
        self.visited_urls: List[str] = []
        self.errors: List[str] = []
        self.total_tokens_used = 0
        self.start_time = time.time()
        self.success = False
        
        # Telemetry & artifact accumulation
        self.screenshots: List[str] = []
        self.artifacts: List[str] = []
        self.verification_data: Dict[str, Any] = {}

    def add_step(
        self,
        thought: str,
        command: str,
        selector: Optional[str],
        text: Optional[str],
        result_message: str,
        success: bool,
        duration_ms: float,
        dom_simplify_time_ms: float = 0.0,
        llm_inference_time_ms: float = 0.0,
    ) -> None:
        """Append a completed step execution record to state history."""
        step = StepExecution(
            step_number=self.current_step,
            thought=thought,
            command=command,
            selector=selector,
            text=text,
            result_message=result_message,
            success=success,
            duration_ms=duration_ms,
            dom_simplify_time_ms=dom_simplify_time_ms,
            llm_inference_time_ms=llm_inference_time_ms,
        )
        # Handle both dict-like and object representations for internal compatibility
        self.history.append(step.to_dict())
        self.current_step += 1
        if not success:
            self.errors.append(result_message)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize PlannerState to dictionary."""
        return {
            "goal": self.goal,
            "history": self.history,
            "current_step": self.current_step,
            "visited_urls": self.visited_urls,
            "errors": self.errors,
            "total_tokens_used": self.total_tokens_used,
            "start_time": self.start_time,
            "success": self.success,
            "screenshots": self.screenshots,
            "artifacts": self.artifacts,
            "verification_data": self.verification_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlannerState":
        """Deserialize PlannerState from dictionary."""
        state = cls(data["goal"])
        state.history = data.get("history", [])
        state.current_step = data.get("current_step", 1)
        state.visited_urls = data.get("visited_urls", [])
        state.errors = data.get("errors", [])
        state.total_tokens_used = data.get("total_tokens_used", 0)
        state.start_time = data.get("start_time", time.time())
        state.success = data.get("success", False)
        state.screenshots = data.get("screenshots", [])
        state.artifacts = data.get("artifacts", [])
        state.verification_data = data.get("verification_data", {})
        return state

    def record_visit(self, url: str) -> None:
        """Track visited URL to prevent loops and compute trajectory paths."""
        if url and (not self.visited_urls or self.visited_urls[-1] != url):
            self.visited_urls.append(url)

    def get_summary_text(self) -> str:
        """Render step history summary as readable text context for LLM prompt."""
        if not self.history:
            return "No actions taken yet."

        summary_lines = []
        for step in self.history:
            status = "SUCCESS" if step["success"] else f"FAILED: {step['result']}"
            summary_lines.append(
                f"Step {step['step']}:\n"
                f"  Thought: {step['thought']}\n"
                f"  Action: {step['command']} (selector: {step['selector']}, val: {step['text']})\n"
                f"  Result: {status}"
            )
        return "\n".join(summary_lines)

    def get_elapsed_time_ms(self) -> float:
        """Calculate total planner execution time in milliseconds."""
        return (time.time() - self.start_time) * 1000.0
