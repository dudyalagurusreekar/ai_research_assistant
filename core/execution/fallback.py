"""ToolFallbackEngine — graceful degradation and failover engine.

Intercepts tool execution failures and automatically re-routes execution to
secondary or tertiary fallback tools. Implements a circuit breaker pattern
to temporarily lock out unstable tools after consecutive failures.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from core.execution.models.result import ExecutionResult, ExecutionStatus, FallbackEvent
from core.execution.registry import AdaptiveToolRegistry
from infrastructure.logging.logger import StructuredLogger

DEFAULT_FALLBACK_CHAINS: Dict[str, List[str]] = {
    "search_tool": ["browser_tool", "python_interpreter"],
    "browser_tool": ["search_tool", "python_interpreter"],
    "document_tool": ["file_reader_tool", "python_interpreter"],
    "code_tool": ["python_interpreter"],
    "vision_tool": ["python_interpreter"],
    "memory_tool": ["python_interpreter"],
    "report_tool": ["python_interpreter"],
}


class ToolFallbackEngine:
    """Manages automatic failover chains and tool circuit breakers."""

    def __init__(
        self,
        registry: Optional[AdaptiveToolRegistry] = None,
        circuit_breaker_threshold: int = 3,
    ) -> None:
        self.registry = registry or AdaptiveToolRegistry()
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.fallback_events: List[FallbackEvent] = []
        self._fallback_chains = dict(DEFAULT_FALLBACK_CHAINS)
        self._logger = StructuredLogger("ToolFallbackEngine")

    def register_fallback_chain(self, primary_tool: str, fallbacks: List[str]) -> None:
        """Define or overwrite the fallback chain for a primary tool."""
        self._fallback_chains[primary_tool] = list(fallbacks)

    def get_fallbacks(self, primary_tool: str) -> List[str]:
        """Return ordered fallback tool names for a primary tool."""
        # Check descriptor first, fallback to class dict
        desc = self.registry.get_descriptor(primary_tool)
        if desc and desc.fallback_tools:
            return [t for t in desc.fallback_tools if t != primary_tool]
        return self._fallback_chains.get(primary_tool, ["python_interpreter"])

    def is_circuit_open(self, tool_name: str) -> bool:
        """Return True if the circuit breaker is open (tool disabled due to failures)."""
        desc = self.registry.get_descriptor(tool_name)
        if not desc:
            return False
        return desc.consecutive_failures >= self.circuit_breaker_threshold

    def execute_with_fallback(
        self,
        primary_tool: str,
        action: str,
        parameters: Dict[str, Any],
        task_id: str,
        executors: Dict[str, Callable[[str, Dict[str, Any]], Any]],
    ) -> ExecutionResult:
        """Execute a tool with automatic failover to fallback tools if it fails or has an open circuit.

        Args:
            primary_tool: Primary tool name.
            action: Action string.
            parameters: Parameter dict.
            task_id: Sub-task identifier.
            executors: Dict mapping tool_name -> callable(action, params).

        Returns:
            ExecutionResult indicating outcome, latency, and whether fallback was used.
        """
        candidate_tools = [primary_tool] + self.get_fallbacks(primary_tool)

        last_error = ""
        fallback_used = None

        for idx, tool_name in enumerate(candidate_tools):
            # Check circuit breaker
            if self.is_circuit_open(tool_name):
                self._logger.warning(
                    f"Circuit breaker OPEN for tool '{tool_name}' (skipping to next candidate)"
                )

                event = FallbackEvent(
                    primary_tool=primary_tool,
                    fallback_tool=candidate_tools[idx + 1] if idx + 1 < len(candidate_tools) else "none",
                    task_id=task_id,
                    reason=f"Circuit breaker open for {tool_name}",
                    success=False,
                )
                self.fallback_events.append(event)
                continue

            executor = executors.get(tool_name)
            if not executor:
                self._logger.debug(f"No executor available for '{tool_name}'; trying fallback")
                continue

            start_time = time.perf_counter()
            try:
                if idx > 0:
                    fallback_used = tool_name
                    self._logger.info(
                        f"Executing FALLBACK tool '{tool_name}' for task '{task_id}' "
                        f"(primary '{primary_tool}' failed)"
                    )

                result_data = executor(action, parameters)
                latency_ms = (time.perf_counter() - start_time) * 1000.0

                # Record success in registry
                self.registry.record_outcome(tool_name, success=True, latency_ms=latency_ms)

                if fallback_used:
                    event = FallbackEvent(
                        primary_tool=primary_tool,
                        fallback_tool=fallback_used,
                        task_id=task_id,
                        reason=f"Primary tool failed: {last_error}",
                        success=True,
                    )
                    self.fallback_events.append(event)

                status = ExecutionStatus.DEGRADED if fallback_used else ExecutionStatus.SUCCESS

                return ExecutionResult(
                    task_id=task_id,
                    tool_name=primary_tool,
                    action=action,
                    status=status,
                    output=result_data,
                    latency_ms=latency_ms,
                    fallback_used=fallback_used,
                )

            except Exception as e:
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                last_error = str(e)

                # Record failure in registry
                self.registry.record_outcome(tool_name, success=False, latency_ms=latency_ms, error_message=last_error)

                self._logger.warning(
                    f"Tool '{tool_name}' failed for task '{task_id}': {e}. "
                    f"Attempting fallback..."
                )

        # All candidates failed
        return ExecutionResult(
            task_id=task_id,
            tool_name=primary_tool,
            action=action,
            status=ExecutionStatus.FAILURE,
            output=None,
            latency_ms=0.0,
            error_message=f"All tools in fallback chain failed. Last error: {last_error}",
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize fallback statistics for audit log."""
        return {
            "total_fallback_events": len(self.fallback_events),
            "successful_fallbacks": sum(1 for e in self.fallback_events if e.success),
            "events": [e.to_dict() for e in self.fallback_events],
        }
