"""ExecutionIntegration — facade for Sprint 2 Adaptive Execution Subsystem.

Combines AdaptiveToolRegistry, ToolResultCache, ToolFallbackEngine,
AdaptiveToolSelectionEngine, and ExecutionOptimizationEngine into a unified
high-level interface.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from core.execution.cache import ToolResultCache
from core.execution.fallback import ToolFallbackEngine
from core.execution.models.policy import ExecutionPolicy
from core.execution.models.result import ExecutionResult, ExecutionStatus
from core.execution.optimizer import ExecutionOptimizationEngine, OptimizedExecutionPlan
from core.execution.registry import AdaptiveToolRegistry
from core.execution.selection_engine import AdaptiveToolSelectionEngine
from core.planner.models.context import PlannerContext
from infrastructure.logging.logger import StructuredLogger


class ExecutionIntegration:
    """Unified integration facade for adaptive execution optimization."""

    def __init__(
        self,
        policy: Optional[ExecutionPolicy] = None,
        registry: Optional[AdaptiveToolRegistry] = None,
        cache: Optional[ToolResultCache] = None,
    ) -> None:
        self.policy = policy or ExecutionPolicy()
        self.registry = registry or AdaptiveToolRegistry()
        self.cache = cache or ToolResultCache(
            default_ttl_seconds=self.policy.default_ttl_seconds
        )
        self.fallback_engine = ToolFallbackEngine(
            registry=self.registry,
            circuit_breaker_threshold=self.policy.circuit_breaker_threshold,
        )
        self.selection_engine = AdaptiveToolSelectionEngine(
            registry=self.registry,
            policy=self.policy,
        )
        self.optimizer = ExecutionOptimizationEngine(
            registry=self.registry,
            cache=self.cache,
            fallback_engine=self.fallback_engine,
            policy=self.policy,
        )
        self._logger = StructuredLogger("ExecutionIntegration")

    def select_tools(self, ctx: PlannerContext) -> None:
        """Run adaptive tool selection on PlannerContext."""
        self.selection_engine.select(ctx)

    def optimize_execution(self, ctx: PlannerContext) -> OptimizedExecutionPlan:
        """Produce an OptimizedExecutionPlan from PlannerContext."""
        return self.optimizer.optimize(ctx)

    def execute_task(
        self,
        task_id: str,
        tool_name: str,
        action: str,
        parameters: Dict[str, Any],
        executors: Dict[str, Callable[[str, Dict[str, Any]], Any]],
    ) -> ExecutionResult:
        """Execute a tool with automatic cache lookup, fallback chains, and metrics updating."""
        # 1. Check cache if enabled
        if self.policy.enable_caching:
            desc = self.registry.get_descriptor(tool_name)
            est_lat = desc.avg_actual_latency_ms if desc else 1000.0
            cached_res = self.cache.get(
                tool_name=tool_name,
                action=action,
                parameters=parameters,
                estimated_latency_ms=est_lat,
            )
            if cached_res:
                cached_res.task_id = task_id
                return cached_res

        # 2. Execute with fallback support if enabled
        if self.policy.enable_fallbacks:
            result = self.fallback_engine.execute_with_fallback(
                primary_tool=tool_name,
                action=action,
                parameters=parameters,
                task_id=task_id,
                executors=executors,
            )
        else:
            # Direct execution without fallback
            executor = executors.get(tool_name)
            if not executor:
                return ExecutionResult(
                    task_id=task_id,
                    tool_name=tool_name,
                    action=action,
                    status=ExecutionStatus.FAILURE,
                    error_message=f"No executor found for tool '{tool_name}'",
                )
            try:
                out = executor(action, parameters)
                result = ExecutionResult(
                    task_id=task_id,
                    tool_name=tool_name,
                    action=action,
                    status=ExecutionStatus.SUCCESS,
                    output=out,
                )
            except Exception as e:
                result = ExecutionResult(
                    task_id=task_id,
                    tool_name=tool_name,
                    action=action,
                    status=ExecutionStatus.FAILURE,
                    error_message=str(e),
                )

        # 3. Store result in cache if successful
        if result.status == ExecutionStatus.SUCCESS and self.policy.enable_caching:
            self.cache.put(
                tool_name=tool_name,
                action=action,
                parameters=parameters,
                output=result.output,
            )

        return result

    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Return combined execution telemetry for logs and benchmarks."""
        return {
            "registry": self.registry.to_dict(),
            "cache": self.cache.to_dict(),
            "fallbacks": self.fallback_engine.to_dict(),
        }
