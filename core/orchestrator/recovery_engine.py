"""Global Failure Recovery Engine for retry logic and graceful degradation."""

import asyncio
from typing import Any, Callable, Coroutine
from infrastructure.logging.logger import StructuredLogger
from core.utils.execution_context import UnifiedExecutionContext
from core.models.tool_result import ToolResult


class GlobalRecoveryEngine:
    """Manages automatic retries, fallbacks, and graceful degradation for tool execution."""

    def __init__(self, max_retries: int = 3, base_backoff_ms: int = 1000):
        self.max_retries = max_retries
        self.base_backoff_ms = base_backoff_ms
        self._logger = StructuredLogger("GlobalRecoveryEngine")

    async def execute_with_recovery(
        self,
        tool_name: str,
        func: Callable[..., Coroutine[Any, Any, ToolResult]],
        *args: Any,
        **kwargs: Any
    ) -> ToolResult:
        """Execute a tool function with automatic retries and execution context."""
        session_id = kwargs.pop('session_id', None)
        context = UnifiedExecutionContext(name=tool_name, session_id=session_id)

        attempt = 0
        while attempt <= self.max_retries:
            try:
                # Execute the function within the unified context
                kwargs['retry_count'] = attempt
                result = await context.execute_async(func, *args, **kwargs)
                return result

            except Exception as e:
                attempt += 1
                if attempt > self.max_retries:
                    self._logger.error(f"Max retries ({self.max_retries}) exceeded for {tool_name}. Failing gracefully.")
                    return ToolResult(
                        tool_name=tool_name,
                        success=False,
                        data=None,
                        error_message=f"Operation failed after {self.max_retries} retries. Final Error: {str(e)}",
                        metadata={"degraded": True, "final_error": str(e)}
                    )

                backoff = self.base_backoff_ms * (2 ** (attempt - 1)) / 1000.0
                self._logger.warning(f"Attempt {attempt} failed for {tool_name}. Retrying in {backoff} seconds... Error: {str(e)}")
                await asyncio.sleep(backoff)
                
        return ToolResult(
            tool_name=tool_name,
            success=False,
            data=None,
            error_message="Recovery engine failed to execute.",
        )
