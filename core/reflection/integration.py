"""ReflectionIntegration — facade connecting the Reflection Engine to Agent Runtimes.

Exposes high-level reflection methods for post-execution critique, conflict resolution,
and DAG graph modification.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.planner.models.context import PlannerContext
from core.reflection.engine import ReflectionEngine
from core.reflection.models.policy import ReflectionPolicy
from core.reflection.models.reflection import ReflectionDecision
from infrastructure.logging.logger import StructuredLogger


class ReflectionIntegration:
    """Facade for integrating reflection evaluation into research workflows."""

    def __init__(
        self,
        engine: Optional[ReflectionEngine] = None,
        policy: Optional[ReflectionPolicy] = None,
    ) -> None:
        self.engine = engine or ReflectionEngine(policy=policy)
        self._logger = StructuredLogger("ReflectionIntegration")

    def reflect_and_correct(
        self,
        ctx: PlannerContext,
        task_outputs: Dict[str, Any],
        iteration: int = 1,
    ) -> ReflectionDecision:
        """Run post-execution evaluation and apply adaptive replanning if needed."""
        return self.engine.evaluate_and_reflect(ctx, task_outputs, iteration=iteration)

    def get_summary(self) -> Dict[str, Any]:
        """Return reflection audit statistics."""
        return self.engine.decision_recorder.to_dict()
