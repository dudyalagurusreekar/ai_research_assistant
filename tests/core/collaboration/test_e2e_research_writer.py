"""End-to-End Test: Research Agent + Writer Agent Workflow."""

import pytest

from core.collaboration import MultiAgentCollaborationEngine


def test_e2e_research_writer_workflow():
    engine = MultiAgentCollaborationEngine()
    ctx = engine.execute_preset_workflow(
        workflow_name="research_writer",
        query="State of the Art in Transformer Attention Mechanisms 2026",
    )

    assert ctx.status.value == "completed"
    assert len(ctx.task_outputs) == 2

    workspace = engine.workspace
    assert workspace.has("research_summary")
    assert workspace.has("final_report")

    report = workspace.get("final_report")
    assert "# State of the Art in Transformer Attention Mechanisms 2026" in report
    assert "Research Findings" in report
