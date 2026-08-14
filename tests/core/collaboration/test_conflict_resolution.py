"""Unit tests for ConflictResolutionEngine detection and reconciliation strategies."""

import pytest

from core.collaboration.components.conflict_resolution import ConflictResolutionEngine
from core.collaboration.models.conflict import ConflictType, ResolutionStrategy
from core.collaboration.models.context import AgentOutput


def test_detect_quality_gate_failure_conflict():
    engine = ConflictResolutionEngine()

    outputs = {
        "task_1": AgentOutput(task_id="task_1", agent_id="agent_a", status="completed", confidence_score=0.95, result="Good result"),
        "task_2": AgentOutput(task_id="task_2", agent_id="agent_b", status="failed", error_message="Task timeout", confidence_score=0.0),
    }

    conflicts = engine.detect_conflicts(outputs)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.QUALITY_GATE_FAILURE
    assert "agent_b" in conflicts[0].involved_agent_ids


def test_detect_contradictory_data_conflict():
    engine = ConflictResolutionEngine()

    outputs = {
        "task_1": AgentOutput(task_id="task_1", agent_id="research_agent", status="completed", confidence_score=0.8, result={"accuracy": 0.85}),
        "task_2": AgentOutput(task_id="task_2", agent_id="data_agent", status="completed", confidence_score=0.95, result={"accuracy": 0.96}),
    }

    conflicts = engine.detect_conflicts(outputs)
    assert len(conflicts) >= 1
    assert conflicts[0].conflict_type == ConflictType.CONTRADICTORY_DATA


def test_resolve_conflict_confidence_weighted():
    engine = ConflictResolutionEngine()

    outputs = {
        "task_1": AgentOutput(task_id="task_1", agent_id="agent_low", status="completed", confidence_score=0.75, result={"key": "val1"}),
        "task_2": AgentOutput(task_id="task_2", agent_id="agent_high", status="completed", confidence_score=0.95, result={"key": "val2"}),
    }

    conflicts = engine.detect_conflicts(outputs)
    conflict = conflicts[0]

    resolved = engine.resolve_conflict(conflict, outputs, strategy=ResolutionStrategy.CONFIDENCE_WEIGHTED)
    assert resolved.is_resolved is True
    assert resolved.resolved_output == {"key": "val2"}
    assert resolved.confidence_score == 0.95


def test_resolve_conflict_reviewer_override():
    engine = ConflictResolutionEngine()

    outputs = {
        "task_1": AgentOutput(task_id="task_1", agent_id="worker_agent", status="completed", confidence_score=0.70, result="Draft claim"),
    }
    reviewer_output = AgentOutput(
        task_id="task_rev", agent_id="reviewer_agent", status="completed", confidence_score=0.98, result="Verified claim"
    )

    conflicts = engine.detect_conflicts(outputs)
    assert len(conflicts) == 0  # no automatic conflict, create explicit one

    conflict = engine.detect_conflicts({"t_fail": AgentOutput(task_id="t_fail", agent_id="worker", status="failed", confidence_score=0.0)})[0]

    resolved = engine.resolve_conflict(conflict, outputs, strategy=ResolutionStrategy.REVIEWER_OVERRIDE, reviewer_output=reviewer_output)
    assert resolved.is_resolved is True
    assert resolved.resolved_output == "Verified claim"
    assert resolved.confidence_score == 0.98
