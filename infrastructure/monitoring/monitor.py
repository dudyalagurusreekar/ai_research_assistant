"""Infrastructure Monitor for tracking telemetry, tool usage, errors, and tokens."""

import time
from typing import Any, Dict, List, Optional


class InfrastructureMonitor:
    """Tracks execution timing, token consumption, error rates, tool statistics, and performance counters."""

    def __init__(self) -> None:
        self.total_tokens: int = 0
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.tool_calls: Dict[str, int] = {}
        self.tool_durations_ms: Dict[str, List[float]] = {}
        self.errors: List[Dict[str, Any]] = []
        self.counters: Dict[str, int] = {}

    def record_tokens(self, prompt: int, completion: int) -> None:
        """Record token consumption."""
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += (prompt + completion)

    def record_tool_execution(self, tool_name: str, duration_ms: float, success: bool = True) -> None:
        """Record tool execution statistics and timing."""
        self.tool_calls[tool_name] = self.tool_calls.get(tool_name, 0) + 1
        if tool_name not in self.tool_durations_ms:
            self.tool_durations_ms[tool_name] = []
        self.tool_durations_ms[tool_name].append(duration_ms)

        if not success:
            self.increment_counter(f"tool_error.{tool_name}")

    def record_error(self, error_type: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Record an error occurrence."""
        self.errors.append({
            "timestamp": time.time(),
            "error_type": error_type,
            "message": message,
            "context": context or {},
        })
        self.increment_counter("total_errors")

    def increment_counter(self, name: str, amount: int = 1) -> None:
        """Increment a performance counter."""
        self.counters[name] = self.counters.get(name, 0) + amount

    def get_summary(self) -> Dict[str, Any]:
        """Return aggregated infrastructure telemetry summary."""
        avg_tool_latencies = {
            t: sum(durs) / max(1, len(durs)) for t, durs in self.tool_durations_ms.items()
        }
        return {
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "tool_calls": self.tool_calls,
            "avg_tool_latencies_ms": avg_tool_latencies,
            "error_count": len(self.errors),
            "counters": self.counters,
        }
