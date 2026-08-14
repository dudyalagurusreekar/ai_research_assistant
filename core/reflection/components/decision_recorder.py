"""ReflectionDecisionRecorder — structured audit trail for reflection decisions.

Records all reflection assessments, plan critiques, decision rationales, and execution graph
modifications for observability and telemetry export.
"""

from __future__ import annotations

from typing import Any, Dict, List

from core.reflection.models.reflection import ReflectionAction, ReflectionDecision
from infrastructure.logging.logger import StructuredLogger


class ReflectionDecisionRecorder:
    """Audit logger for tracking reflection decisions across requests."""

    def __init__(self) -> None:
        self._history: List[ReflectionDecision] = []
        self._logger = StructuredLogger("ReflectionDecisionRecorder")

    def record(self, decision: ReflectionDecision) -> None:
        """Record a ReflectionDecision in history."""
        self._history.append(decision)
        self._logger.info(
            f"Recorded ReflectionDecision '{decision.decision_id}' -- Action: {decision.action.value.upper()} "
            f"(Rationale: {decision.rationale[:60]})"
        )

    def list_decisions(self) -> List[ReflectionDecision]:
        """Return full history of decisions."""
        return list(self._history)

    def get_latest(self) -> Optional[ReflectionDecision]:
        """Return the most recent decision or None."""
        return self._history[-1] if self._history else None

    def to_dict(self) -> Dict[str, Any]:
        """Return telemetry summary dict."""
        actions_count = {act.value: 0 for act in ReflectionAction}
        for d in self._history:
            actions_count[d.action.value] = actions_count.get(d.action.value, 0) + 1

        total_pruned = sum(len(d.nodes_to_remove) for d in self._history)
        total_injected = sum(len(d.nodes_to_add) for d in self._history)

        return {
            "total_decisions": len(self._history),
            "action_breakdown": actions_count,
            "total_nodes_pruned": total_pruned,
            "total_tasks_injected": total_injected,
            "decisions": [d.to_dict() for d in self._history[-5:]],
        }
