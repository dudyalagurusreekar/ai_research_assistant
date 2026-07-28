"""Execution Tracer for fine-grained workflow step and tool invocation recording."""

import time
from typing import Dict
from tools.benchmark.interfaces.benchmark_interfaces import IExecutionTracer
from tools.benchmark.models.benchmark_models import ExecutionTrace, ExecutionStep
from infrastructure.logging.logger import StructuredLogger


class ExecutionTracer(IExecutionTracer):
    """Captures fine-grained step execution telemetry, tool invocations, timing, and error propagation."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("ExecutionTracer")
        self._active_traces: Dict[str, ExecutionTrace] = {}
        self._start_times: Dict[str, float] = {}

    def start_trace(self, task_id: str) -> ExecutionTrace:
        """Initialize a new trace context for a task."""
        trace = ExecutionTrace(task_id=task_id)
        self._active_traces[trace.trace_id] = trace
        self._start_times[trace.trace_id] = time.time()
        self._logger.debug(f"Started trace '{trace.trace_id}' for task '{task_id}'")
        return trace

    def record_step(self, trace_id: str, step: ExecutionStep) -> None:
        """Record an execution step to an active trace."""
        trace = self._active_traces.get(trace_id)
        if not trace:
            self._logger.warning(f"Attempted to record step for unknown trace_id '{trace_id}'")
            return

        trace.steps.append(step.to_dict())

        if step.tool_name and step.tool_name not in trace.tool_invocations:
            trace.tool_invocations.append(step.tool_name)

        if step.retry_count > 0:
            trace.retry_history.append({
                "step_id": step.step_id,
                "tool_name": step.tool_name,
                "retries": step.retry_count,
            })

        if step.error:
            trace.error_propagation.append(f"{step.tool_name or step.step_type}: {step.error}")

        trace.timing_info[step.step_id] = step.duration_ms

    def finalize_trace(self, trace_id: str, final_answer: str) -> ExecutionTrace:
        """Finalize and return completed execution trace."""
        trace = self._active_traces.get(trace_id)
        if not trace:
            # Fallback if trace was not explicitly initialized
            trace = ExecutionTrace(final_answer=final_answer)
            return trace

        start_time = self._start_times.pop(trace_id, time.time())
        trace.execution_time_ms = round((time.time() - start_time) * 1000, 2)
        trace.final_answer = final_answer

        self._active_traces.pop(trace_id, None)
        self._logger.debug(f"Finalized trace '{trace_id}' in {trace.execution_time_ms}ms")
        return trace
