"""End-to-End test for AutonomousResearchEngine pipeline."""

import pytest

from core.workflow.engine import AutonomousResearchEngine
from core.workflow.models.context import WorkflowStage, WorkflowStatus
from tools.workflow.research_workflow_tool import ResearchWorkflowTool


def test_e2e_autonomous_research_workflow():
    engine = AutonomousResearchEngine()
    query = "Research quantum computing algorithms, compare Shor's vs Grover's complexity"

    ctx = engine.execute_autonomous_research(query)

    assert ctx.status == WorkflowStatus.COMPLETED
    assert ctx.stage == WorkflowStage.COMPLETED
    assert ctx.goal is not None
    assert len(ctx.questions) >= 4
    assert ctx.report is not None
    assert "Autonomous Research Report" in ctx.report.title
    assert len(ctx.report.markdown_content) > 100


def test_e2e_research_workflow_tool_integration():
    tool = ResearchWorkflowTool()
    res = tool.execute("execute_research", query="Analyze AI Transformer Benchmarks")

    assert res["status"] == "success"
    assert res["stage"] == "completed"
    assert res["questions_resolved"] >= 4
