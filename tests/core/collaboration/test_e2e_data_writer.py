"""End-to-End Test: Data Agent + Writer Agent Workflow."""

import pytest

from core.collaboration import MultiAgentCollaborationEngine


def test_e2e_data_writer_workflow():
    engine = MultiAgentCollaborationEngine()
    ctx = engine.execute_preset_workflow(
        workflow_name="data_writer",
        query="Benchmark Execution Metrics for ARA Version 2.5",
        payload={
            "records": [
                {"metric": "planning_latency_ms", "baseline": 45.0, "v2_5": 1.8},
                {"metric": "tool_context_reduction", "baseline": 0.0, "v2_5": 0.74},
            ]
        },
    )

    assert ctx.status.value == "completed"
    assert len(ctx.task_outputs) == 2

    workspace = engine.workspace
    assert workspace.has("data_stats")
    assert workspace.has("chart_svg")
    assert workspace.has("final_report")

    report = workspace.get("final_report")
    assert "Quantitative Data Analysis" in report
    assert "<svg" in report
