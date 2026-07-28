"""Unified Execution Context for recording structured logging and metrics."""

import time
from typing import Any, Callable, Coroutine, Optional
from infrastructure.logging.logger import StructuredLogger
from core.utils.time_utils import utc_now
from core.models.tool_result import ToolResult


class UnifiedExecutionContext:
    """Wraps execution of tools or operations to record structured metrics and logs."""

    def __init__(self, name: str, session_id: Optional[str] = None, trace_id: Optional[str] = None):
        self.name = name
        self.session_id = session_id
        self.trace_id = trace_id
        self._logger = StructuredLogger(f"ExecutionContext.{name}")
        self._logger.set_context(session_id=session_id, trace_id=trace_id)

    async def execute_async(self, func: Callable[..., Coroutine[Any, Any, Any]], *args: Any, **kwargs: Any) -> Any:
        """Execute an asynchronous function within the context, recording metrics."""
        start_time = time.time()
        start_timestamp = utc_now().isoformat()
        retry_count = kwargs.pop('retry_count', 0)

        try:
            result = await func(*args, **kwargs)
            end_time = time.time()
            execution_time_ms = (end_time - start_time) * 1000

            if isinstance(result, ToolResult):
                result.execution_time_ms = execution_time_ms
                result.metadata["start_timestamp"] = start_timestamp
                result.metadata["end_timestamp"] = utc_now().isoformat()
                result.metadata["retry_count"] = retry_count

            self._logger.info(
                f"Successfully executed {self.name}",
                extra_fields={
                    "start_timestamp": start_timestamp,
                    "end_timestamp": utc_now().isoformat(),
                    "execution_time_ms": execution_time_ms,
                    "status": "success",
                    "retry_count": retry_count,
                    "operation": self.name
                }
            )
            return result

        except Exception as e:
            end_time = time.time()
            execution_time_ms = (end_time - start_time) * 1000

            self._logger.error(
                f"Execution failed for {self.name}: {str(e)}",
                extra_fields={
                    "start_timestamp": start_timestamp,
                    "end_timestamp": utc_now().isoformat(),
                    "execution_time_ms": execution_time_ms,
                    "status": "failure",
                    "retry_count": retry_count,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "operation": self.name
                }
            )
            
            # Note: We re-raise the exception, the RecoveryEngine will catch it.
            raise
