"""ConstraintEnforcer — establishes execution constraints and stopping criteria.

Computes step limits, token budgets, timeouts, and stopping conditions based
on the complexity estimate and intent classification.
"""

from __future__ import annotations

from core.planner.interfaces.base import IConstraintEnforcer
from core.planner.models.context import ExecutionConstraints, PlannerContext, QueryIntent
from infrastructure.logging.logger import StructuredLogger


class ConstraintEnforcer(IConstraintEnforcer):
    """Determines execution constraints from complexity estimates and intent."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("ConstraintEnforcer")

    @property
    def component_name(self) -> str:
        return "ConstraintEnforcer"

    def enforce(self, ctx: PlannerContext) -> ExecutionConstraints:
        """Compute and attach execution constraints to the planning context."""
        intent = ctx.intent or QueryIntent.AMBIGUOUS
        complexity = ctx.complexity

        # Base constraints
        max_steps = 15
        max_tool_calls = 10
        max_tokens = 8192
        timeout = 300.0
        allow_parallel = True
        require_verification = True
        max_retries = 2

        # Adjust based on complexity
        if complexity:
            max_steps = min(complexity.max_step_limit, 20)
            max_tool_calls = min(complexity.estimated_tool_calls + 3, 15)
            max_tokens = min(complexity.estimated_tokens + 2000, 16384)
            timeout = min(complexity.estimated_latency_seconds * 3.0, 600.0)

        # Intent-specific adjustments
        if intent == QueryIntent.CODE_EXECUTION:
            require_verification = False  # code output is self-verifying
            max_retries = 3  # code may need more retries
        elif intent == QueryIntent.MEMORY_OPERATION:
            max_steps = min(max_steps, 5)
            timeout = min(timeout, 60.0)
            require_verification = False
        elif intent == QueryIntent.FACTUAL_QA:
            require_verification = True  # facts should be verified
        elif intent == QueryIntent.MULTI_STEP_RESEARCH:
            max_steps = max(max_steps, 10)
            timeout = max(timeout, 300.0)
            allow_parallel = True

        # Stopping criteria
        stopping_criteria = [
            "all_sub_tasks_completed",
            "max_steps_reached",
            "timeout_exceeded",
            "critical_error_encountered",
        ]
        if require_verification:
            stopping_criteria.append("verification_passed")

        constraints = ExecutionConstraints(
            max_steps=max_steps,
            max_tool_calls=max_tool_calls,
            max_tokens=max_tokens,
            timeout_seconds=timeout,
            allow_parallel=allow_parallel,
            require_verification=require_verification,
            max_retries_per_step=max_retries,
            stopping_criteria=stopping_criteria,
        )

        ctx.constraints = constraints
        ctx.add_trace(
            stage="constraint_enforcement",
            message=f"Constraints enforced: max_steps={max_steps}, timeout={timeout:.0f}s, "
                    f"parallel={allow_parallel}, verification={require_verification}",
            data={
                "max_steps": max_steps,
                "max_tool_calls": max_tool_calls,
                "max_tokens": max_tokens,
                "timeout_seconds": timeout,
                "allow_parallel": allow_parallel,
                "require_verification": require_verification,
                "stopping_criteria": stopping_criteria,
            },
        )
        self._logger.info(
            f"Constraints enforced: steps={max_steps}, timeout={timeout:.0f}s"
        )
        return constraints
