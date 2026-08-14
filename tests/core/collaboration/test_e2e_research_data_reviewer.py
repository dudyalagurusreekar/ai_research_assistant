"""End-to-End Test: Research Agent + Data Agent + Reviewer Agent Workflow."""

import pytest

from core.collaboration import MultiAgentCollaborationEngine


def test_e2e_research_data_reviewer_workflow():
    engine = MultiAgentCollaborationEngine()
    ctx = engine.execute_preset_workflow(
        workflow_name="research_data_reviewer",
        query="Impact of Multi-Agent Systems on Complex Research Quality",
    )

    assert ctx.status.value == "completed"
    assert len(ctx.task_outputs) == 3

    # Parallel wave verification (wave 0 has 2 parallel tasks: Research + Data)
    waves = [t.parallel_wave for t in ctx.task_assignments]
    assert waves == [0, 0, 1]

    workspace = engine.workspace
    assert workspace.has("research_summary")
    assert workspace.has("data_stats")
    assert workspace.has("review_result")

    review = workspace.get("review_result")
    assert review["verification_passed"] is True
    assert review["quality_score"] >= 0.90
