"""ReasoningEvaluator — assesses logical completeness and hallucination risk.

Evaluates intermediate sub-task outputs against the original query intent, calculating
completeness scores, coherence metrics, hallucination risk levels, and unaddressed requirements.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from core.planner.models.context import PlannerContext
from core.reflection.models.reflection import ReasoningAssessment
from infrastructure.logging.logger import StructuredLogger


class ReasoningEvaluator:
    """Evaluates logical reasoning quality and checks if query requirements are met."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("ReasoningEvaluator")

    def evaluate(self, ctx: PlannerContext, task_outputs: Dict[str, Any]) -> ReasoningAssessment:
        """Evaluate logic completeness and hallucination risk across completed task outputs.

        Args:
            ctx: PlannerContext detailing user query, sub-tasks, and intent.
            task_outputs: Dict mapping task_id / node_id to execution output text/object.

        Returns:
            ReasoningAssessment object containing completeness, coherence, and risk scores.
        """
        if not task_outputs:
            return ReasoningAssessment(
                completeness_score=0.0,
                coherence_score=0.5,
                hallucination_risk_score=0.5,
                confidence_score=0.0,
                unaddressed_aspects=["No task outputs collected"],
            )

        query_lower = ctx.user_query.lower()
        sub_tasks = ctx.sub_tasks

        # 1. Evaluate coverage of sub-tasks
        completed_keys = set(task_outputs.keys())
        expected_task_ids = {t.task_id for t in sub_tasks}
        if ctx.execution_graph:
            # Map node_ids to task_ids so node_id and task_id count as the same subtask
            node_to_task = {n.node_id: n.task_id for n in ctx.execution_graph.nodes.values() if n.task_id}
            completed_task_ids = {node_to_task.get(k, k) for k in completed_keys}
            matched_count = len(completed_task_ids.intersection(expected_task_ids))
        else:
            matched_count = len(completed_keys.intersection(expected_task_ids))

        if not matched_count and task_outputs and expected_task_ids:
            coverage = min(1.0, len(task_outputs) / len(expected_task_ids))
        elif expected_task_ids:
            coverage = matched_count / len(expected_task_ids)
        else:
            coverage = 1.0

        # 2. Extract combined text output
        combined_text = ""
        for out in task_outputs.values():
            if isinstance(out, str):
                combined_text += " " + out.lower()
            elif isinstance(out, dict):
                combined_text += " " + str(out).lower()

        # 3. Check specific requirements (e.g. comparison keywords, document keywords)
        unaddressed: List[str] = []

        if "compare" in query_lower and not any(k in combined_text for k in ["vs", "versus", "comparison", "compared", "difference", "advantage"]):
            unaddressed.append("Comparison aspects not explicitly highlighted")

        if ("pdf" in query_lower or "document" in query_lower or "file" in query_lower) and not any(k in combined_text for k in ["document", "pdf", "summary", "parsed", "content"]):
            unaddressed.append("Document ingestion evidence missing")

        # Calculate completeness score based on coverage and unaddressed aspects
        completeness = max(0.0, min(1.0, coverage - (len(unaddressed) * 0.15)))

        # 4. Assess hallucination risk (high risk if text is very short or unaddressed count > 1)
        hallucination_risk = 0.05
        if len(combined_text.strip()) < 50:
            hallucination_risk += 0.40
        if unaddressed:
            hallucination_risk += 0.20 * len(unaddressed)
        hallucination_risk = min(1.0, hallucination_risk)

        # 5. Coherence score
        coherence = 1.0 - (hallucination_risk * 0.5)

        # 6. Overall confidence score
        confidence = (0.5 * completeness) + (0.3 * coherence) + (0.2 * (1.0 - hallucination_risk))

        assessment = ReasoningAssessment(
            completeness_score=round(completeness, 2),
            coherence_score=round(coherence, 2),
            hallucination_risk_score=round(hallucination_risk, 2),
            confidence_score=round(confidence, 2),
            unaddressed_aspects=unaddressed,
        )

        self._logger.info(
            f"Reasoning Evaluation: completeness={assessment.completeness_score:.2f}, "
            f"confidence={assessment.confidence_score:.2f}, risk={assessment.hallucination_risk_score:.2f}"
        )
        return assessment
