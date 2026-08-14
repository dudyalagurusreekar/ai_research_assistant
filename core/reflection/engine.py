"""ReflectionEngine — main orchestrator for reflection and adaptive reasoning.

Coordinates ReasoningEvaluator, PlanCritic, EvidenceEvaluator, AdaptiveReplanningEngine,
and ReflectionDecisionRecorder to continuously critique and correct execution plans.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.planner.models.context import PlannerContext
from core.reflection.components.decision_recorder import ReflectionDecisionRecorder
from core.reflection.components.evidence_evaluator import EvidenceEvaluator
from core.reflection.components.plan_critic import PlanCritic
from core.reflection.components.reasoning_evaluator import ReasoningEvaluator
from core.reflection.components.replanning_engine import AdaptiveReplanningEngine
from core.reflection.models.policy import ReflectionPolicy
from core.reflection.models.reflection import (
    EvidenceQuality,
    ReflectionAction,
    ReflectionDecision,
)
from infrastructure.logging.logger import StructuredLogger


class ReflectionEngine:
    """Production Reflection Engine evaluating reasoning quality and modifying DAGs."""

    def __init__(
        self,
        reasoning_evaluator: Optional[ReasoningEvaluator] = None,
        plan_critic: Optional[PlanCritic] = None,
        evidence_evaluator: Optional[EvidenceEvaluator] = None,
        replanning_engine: Optional[AdaptiveReplanningEngine] = None,
        decision_recorder: Optional[ReflectionDecisionRecorder] = None,
        policy: Optional[ReflectionPolicy] = None,
    ) -> None:
        self.policy = policy or ReflectionPolicy()
        self.reasoning_evaluator = reasoning_evaluator or ReasoningEvaluator()
        self.plan_critic = plan_critic or PlanCritic()
        self.evidence_evaluator = evidence_evaluator or EvidenceEvaluator()
        self.replanning_engine = replanning_engine or AdaptiveReplanningEngine()
        self.decision_recorder = decision_recorder or ReflectionDecisionRecorder()
        self._logger = StructuredLogger("ReflectionEngine")

    def evaluate_and_reflect(
        self,
        ctx: PlannerContext,
        task_outputs: Dict[str, Any],
        iteration: int = 1,
    ) -> ReflectionDecision:
        """Run post-execution reflection evaluation.

        Args:
            ctx: PlannerContext containing user query, sub-tasks, and execution graph.
            task_outputs: Dict mapping task/node IDs to execution results.
            iteration: Current reflection loop count (1 to max_reflection_loops).

        Returns:
            ReflectionDecision indicating action (PROCEED, PRUNE, REPLAN, etc.) and metrics.
        """
        # 1. Run Evaluators
        evidence_assess = self.evidence_evaluator.evaluate(task_outputs)
        critic_report = self.plan_critic.critique(ctx, task_outputs)
        reasoning_assess = self.reasoning_evaluator.evaluate(ctx, task_outputs)

        nodes_to_add: list[dict[str, Any]] = []
        nodes_to_remove: list[str] = list(critic_report.suggested_prunings)
        action = ReflectionAction.PROCEED
        rationale = "Execution quality meets criteria; proceeding to report synthesis"
        impact_summary = "Zero changes required"

        # 2. Decision Logic Hierarchy
        if iteration > self.policy.max_reflection_loops:
            action = ReflectionAction.PROCEED
            rationale = f"Max reflection loops ({self.policy.max_reflection_loops}) reached; forcing PROCEED"
            impact_summary = "Loop limit reached"
        elif self.policy.enable_conflict_resolution and evidence_assess.conflict_detected:
            action = ReflectionAction.RESOLVE_CONFLICT
            rationale = (
                f"Conflicting claims detected between sources ({', '.join(evidence_assess.conflicting_sources)}). "
                f"Injecting conflict resolution task."
            )
            impact_summary = "Injected conflict resolution sub-task"
            nodes_to_add.append({
                "tool_name": "search_tool",
                "action": "search",
                "title": "Conflict Resolution Search",
                "description": f"Verify conflicting facts between sources: {', '.join(evidence_assess.conflicting_sources)}",
                "parameters": {"query": f"verify conflict {ctx.user_query}"},
            })
        elif evidence_assess.quality in (EvidenceQuality.WEAK, EvidenceQuality.INSUFFICIENT):
            action = ReflectionAction.GATHER_MORE_EVIDENCE
            rationale = f"Evidence quality is {evidence_assess.quality.value} (score={evidence_assess.quality_score:.2f}). Injecting deep evidence gathering."
            impact_summary = "Injected deep evidence sub-task"
            nodes_to_add.append({
                "tool_name": "search_tool",
                "action": "search",
                "title": "Deep Evidence Collection",
                "description": f"Deep search to complement weak evidence for: {ctx.user_query}",
                "parameters": {"query": ctx.user_query},
            })
        elif self.policy.enable_auto_pruning and critic_report.has_issues and nodes_to_remove:
            action = ReflectionAction.PRUNE_STEPS
            rationale = (
                f"Identified {len(critic_report.redundant_node_ids)} redundant and "
                f"{len(critic_report.dead_end_node_ids)} dead-end DAG nodes for pruning."
            )
            impact_summary = f"Pruned {len(nodes_to_remove)} nodes from DAG"
        elif reasoning_assess.completeness_score < self.policy.min_completeness_threshold:
            action = ReflectionAction.REPLAN
            rationale = (
                f"Reasoning completeness score {reasoning_assess.completeness_score:.2f} is below "
                f"threshold {self.policy.min_completeness_threshold:.2f}."
            )
            impact_summary = "Triggered adaptive replan loop"

        decision = ReflectionDecision(
            action=action,
            rationale=rationale,
            impact_summary=impact_summary,
            nodes_to_add=nodes_to_add,
            nodes_to_remove=nodes_to_remove,
            reasoning_assessment=reasoning_assess,
            evidence_assessment=evidence_assess,
            critic_report=critic_report,
            reflection_iteration=iteration,
        )

        # 3. Apply replan changes if required
        if action != ReflectionAction.PROCEED:
            self.replanning_engine.apply_replan(ctx, decision)

        # 4. Record decision
        self.decision_recorder.record(decision)

        self._logger.info(
            f"Reflection Engine decision (iteration {iteration}): Action={action.value.upper()} "
            f"-- {impact_summary}"
        )
        return decision
