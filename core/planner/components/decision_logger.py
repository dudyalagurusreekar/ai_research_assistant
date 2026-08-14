"""DecisionLogger — records structured planning decisions and finalizes metrics.

Provides a clean API for every pipeline component to log its decisions
into the PlannerContext's reasoning trace and decision log.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.planner.interfaces.base import IDecisionLogger
from core.planner.models.context import PlannerContext
from core.planner.models.decision import DecisionLog
from infrastructure.logging.logger import StructuredLogger


class DecisionLogger(IDecisionLogger):
    """Centralized decision recording and metrics finalization."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("DecisionLogger")
        self._decision_log: Optional[DecisionLog] = None

    @property
    def component_name(self) -> str:
        return "DecisionLogger"

    def initialize(self, plan_id: str) -> None:
        """Create a new decision log for the current planning session."""
        self._decision_log = DecisionLog(plan_id=plan_id)

    def log_decision(
        self,
        ctx: PlannerContext,
        stage: str,
        description: str,
        rationale: str = "",
        confidence: float = 1.0,
        data: Dict[str, Any] | None = None,
    ) -> None:
        """Record a structured planning decision."""
        if self._decision_log is None:
            self.initialize(ctx.plan_id)

        assert self._decision_log is not None
        decision = self._decision_log.record(
            stage=stage,
            component=self.component_name,
            description=description,
            rationale=rationale,
            confidence=confidence,
            data=data,
        )

        ctx.add_trace(
            stage=stage,
            message=f"Decision: {description}",
            data={"rationale": rationale, "confidence": confidence, **(data or {})},
        )
        self._logger.debug(
            f"Decision recorded: [{stage}] {description} (confidence={confidence:.2f})"
        )

    def finalize(self, ctx: PlannerContext) -> Dict[str, Any]:
        """Compute final metrics and return the complete decision summary."""
        ctx.metrics.compute_latency()

        summary: Dict[str, Any] = {
            "plan_id": ctx.plan_id,
            "planning_latency_ms": ctx.metrics.planning_latency_ms,
            "stages_completed": ctx.metrics.stages_completed,
            "total_stages": ctx.metrics.total_stages,
            "dag_node_count": ctx.metrics.dag_node_count,
            "dag_edge_count": ctx.metrics.dag_edge_count,
            "parallel_groups": ctx.metrics.parallel_groups,
            "unnecessary_tools_removed": ctx.metrics.unnecessary_tools_removed,
            "error_count": len(ctx.errors),
            "decision_count": self._decision_log.count if self._decision_log else 0,
            "final_stage": ctx.current_stage.value,
            "intent": ctx.intent.value if ctx.intent else None,
            "complexity_score": ctx.complexity.score if ctx.complexity else None,
        }

        if self._decision_log:
            summary["decisions"] = self._decision_log.to_dict()

        ctx.add_trace(
            stage="finalization",
            message=f"Planning finalized in {ctx.metrics.planning_latency_ms:.1f}ms",
            data=summary,
        )
        self._logger.info(
            f"Planning finalized: latency={ctx.metrics.planning_latency_ms:.1f}ms, "
            f"stages={ctx.metrics.stages_completed}/{ctx.metrics.total_stages}, "
            f"errors={len(ctx.errors)}"
        )
        return summary
