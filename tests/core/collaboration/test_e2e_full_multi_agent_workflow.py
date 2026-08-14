"""End-to-End Test: Full Multi-Agent Workflow (Research + Data + Code + Writer + Reviewer)."""

import pytest

from core.collaboration import MultiAgentCollaborationEngine


def test_e2e_full_multi_agent_workflow():
    engine = MultiAgentCollaborationEngine()
    ctx = engine.execute_preset_workflow(
        workflow_name="full_multi_agent",
        query="Comprehensive Benchmark and Analytical Report on Multi-Agent Framework v2.5",
    )

    assert ctx.status.value == "completed"
    assert len(ctx.task_outputs) == 5

    # Check metrics
    metrics = ctx.metrics
    assert metrics.completed_tasks == 5
    assert metrics.failed_tasks == 0
    assert metrics.parallel_speedup_ratio >= 1.0

    workspace = engine.workspace
    assert workspace.has("research_summary")
    assert workspace.has("data_stats")
    assert workspace.has("chart_svg")
    assert workspace.has("generated_code")
    assert workspace.has("final_report")
    assert workspace.has("review_result")

    report = workspace.get("final_report")
    assert "Comprehensive Benchmark and Analytical Report" in report
    assert "Research Findings" in report
    assert "Quantitative Data Analysis" in report
    assert "Algorithmic Verification Code" in report

    review = workspace.get("review_result")
    assert review["verification_passed"] is True
