"""Integration tests for Intelligent Planner → Multi-Agent Orchestrator delegation and DAG execution."""

import pytest

from core.collaboration import (
    MultiAgentCollaborationEngine,
    PlannerCollaborationIntegration,
)
from core.planner.engine import IntelligentPlanningEngine


def test_planner_to_orchestrator_integration():
    planner = IntelligentPlanningEngine()
    collab_engine = MultiAgentCollaborationEngine()
    integration = PlannerCollaborationIntegration(collab_engine)

    query = "Analyze AI Research Assistant version 2.5 benchmarks and compile report"
    planner_ctx = planner.plan(query)

    assert planner_ctx.execution_graph is not None

    assignments = integration.convert_planner_context_to_assignments(planner_ctx)
    assert len(assignments) > 0

    collab_ctx = integration.execute_planner_dag(planner_ctx)
    assert collab_ctx.status.value in ["completed", "running"]
    assert len(collab_ctx.task_outputs) > 0
    assert collab_ctx.metrics.total_tasks == len(assignments)
