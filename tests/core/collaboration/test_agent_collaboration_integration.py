"""Integration tests for multi-agent data sharing and collaboration memory interactions."""

import pytest

from core.collaboration import (
    MultiAgentCollaborationEngine,
    SpecializedDataAgent,
    SpecializedResearchAgent,
    SpecializedWriterAgent,
)


def test_agent_data_sharing_through_workspace():
    collab_engine = MultiAgentCollaborationEngine()

    ctx = collab_engine.execute_preset_workflow(
        workflow_name="research_data_reviewer",
        query="Evaluate LLM Orchestration Engine Performance",
    )

    assert ctx.status.value == "completed"
    workspace = collab_engine.workspace

    assert workspace.has("research_summary")
    assert workspace.has("data_stats")
    assert workspace.has("review_result")

    review = workspace.get("review_result")
    assert review["verification_passed"] is True
