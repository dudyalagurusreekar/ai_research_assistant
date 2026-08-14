"""Integration test for PlannerWorkflowIntegration."""

import pytest

from core.workflow.integration import PlannerWorkflowIntegration


def test_planner_workflow_integration():
    integration = PlannerWorkflowIntegration()
    planner_ctx = integration.delegate_dag_generation("Benchmark Transformer latency")

    assert planner_ctx is not None
    assert hasattr(planner_ctx, "plan_id")
