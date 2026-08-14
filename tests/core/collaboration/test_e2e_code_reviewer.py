"""End-to-End Test: Code Agent + Reviewer Agent Workflow."""

import pytest

from core.collaboration import MultiAgentCollaborationEngine


def test_e2e_code_reviewer_workflow():
    engine = MultiAgentCollaborationEngine()
    ctx = engine.execute_preset_workflow(
        workflow_name="code_reviewer",
        query="Implement Parallel Graph Processing in Python",
    )

    assert ctx.status.value == "completed"
    assert len(ctx.task_outputs) == 2

    workspace = engine.workspace
    assert workspace.has("generated_code")
    assert workspace.has("review_result")

    code = workspace.get("generated_code")
    assert "def solve_task" in code

    review = workspace.get("review_result")
    assert review["verification_passed"] is True
