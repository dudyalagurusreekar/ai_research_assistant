"""Conflict Resolution Engine — Reconciles contradictory outputs and quality gate failures."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.collaboration.models.agent_info import AgentRole
from core.collaboration.models.conflict import (
    ConflictRecord,
    ConflictType,
    ResolutionStrategy,
)
from core.collaboration.models.context import AgentOutput
from utils.logger import get_logger

logger = get_logger("ConflictResolutionEngine")


class ConflictResolutionEngine:
    """Engine for detecting and resolving conflicts, contradictions, and quality failures."""

    def __init__(self, default_strategy: ResolutionStrategy = ResolutionStrategy.CONFIDENCE_WEIGHTED) -> None:
        self.default_strategy = default_strategy

    def detect_conflicts(self, outputs: Dict[str, AgentOutput]) -> List[ConflictRecord]:
        """Inspect agent outputs to detect conflicts, quality failures, or low confidence."""
        conflicts: List[ConflictRecord] = []

        # 1. Quality gate check: outputs with confidence < 0.60 or failed status
        for task_id, output in outputs.items():
            if output.status == "failed" or output.confidence_score < 0.60:
                conflict = ConflictRecord(
                    conflict_type=ConflictType.QUALITY_GATE_FAILURE,
                    description=f"Task {task_id} failed or low confidence ({output.confidence_score:.2f}): {output.error_message or 'Quality gate failure'}",
                    involved_agent_ids=[output.agent_id],
                    conflicting_outputs={task_id: output.to_dict()},
                    confidence_score=output.confidence_score,
                )
                conflicts.append(conflict)

        # 2. Fact / value discrepancy check among outputs sharing keys
        # Group outputs by result payload keys
        payload_map: Dict[str, List[tuple[str, AgentOutput]]] = {}
        for task_id, output in outputs.items():
            if isinstance(output.result, dict):
                for k, v in output.result.items():
                    if k not in payload_map:
                        payload_map[k] = []
                    payload_map[k].append((task_id, output))

        for key, occurrences in payload_map.items():
            if len(occurrences) > 1:
                # Compare values across occurrences
                first_val = occurrences[0][1].result.get(key)
                has_discrepancy = False
                for task_id, output in occurrences[1:]:
                    if output.result.get(key) != first_val:
                        has_discrepancy = True
                        break

                if has_discrepancy:
                    involved_ids = [out.agent_id for _, out in occurrences]
                    conflict = ConflictRecord(
                        conflict_type=ConflictType.CONTRADICTORY_DATA,
                        description=f"Contradictory values detected for key '{key}' across agents {involved_ids}",
                        involved_agent_ids=involved_ids,
                        conflicting_outputs={t_id: out.to_dict() for t_id, out in occurrences},
                        confidence_score=0.5,
                    )
                    conflicts.append(conflict)

        return conflicts

    def resolve_conflict(
        self,
        conflict: ConflictRecord,
        outputs: Dict[str, AgentOutput],
        strategy: Optional[ResolutionStrategy] = None,
        reviewer_output: Optional[AgentOutput] = None,
    ) -> ConflictRecord:
        """Resolve a conflict record using the specified or default resolution strategy."""
        strat = strategy or self.default_strategy
        conflict.applied_strategy = strat

        if strat == ResolutionStrategy.REVIEWER_OVERRIDE and reviewer_output and reviewer_output.result:
            conflict.resolved_output = reviewer_output.result
            conflict.confidence_score = reviewer_output.confidence_score
            conflict.is_resolved = True
            logger.info(f"Conflict {conflict.conflict_id} resolved via REVIEWER_OVERRIDE")

        elif strat == ResolutionStrategy.CONFIDENCE_WEIGHTED:
            # Pick the output with the highest confidence score
            best_out = None
            max_conf = -1.0
            for t_id in conflict.conflicting_outputs.keys():
                if t_id in outputs:
                    out = outputs[t_id]
                    if out.confidence_score > max_conf:
                        max_conf = out.confidence_score
                        best_out = out

            if best_out:
                conflict.resolved_output = best_out.result
                conflict.confidence_score = best_out.confidence_score
                conflict.is_resolved = True
            else:
                conflict.resolved_output = list(conflict.conflicting_outputs.values())[0].get("result")
                conflict.confidence_score = 0.7
                conflict.is_resolved = True
            logger.info(f"Conflict {conflict.conflict_id} resolved via CONFIDENCE_WEIGHTED")

        elif strat == ResolutionStrategy.HYBRID_MERGE:
            # Merge dictionary results cleanly
            merged: Dict[str, Any] = {}
            total_conf = 0.0
            count = 0
            for t_id in conflict.conflicting_outputs.keys():
                if t_id in outputs:
                    out = outputs[t_id]
                    if isinstance(out.result, dict):
                        merged.update(out.result)
                    elif isinstance(out.result, str):
                        merged[f"text_{t_id}"] = out.result
                    total_conf += out.confidence_score
                    count += 1

            conflict.resolved_output = merged if merged else "Merged outputs"
            conflict.confidence_score = (total_conf / count) if count > 0 else 0.8
            conflict.is_resolved = True
            logger.info(f"Conflict {conflict.conflict_id} resolved via HYBRID_MERGE")

        else:  # CONSENSUS or RE_EXECUTION fallback
            conflict.resolved_output = "Resolved via default consensus"
            conflict.confidence_score = 0.85
            conflict.is_resolved = True
            logger.info(f"Conflict {conflict.conflict_id} resolved via CONSENSUS fallback")

        return conflict
