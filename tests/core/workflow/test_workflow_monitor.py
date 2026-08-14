"""Unit test for WorkflowMonitor."""

import pytest

from core.workflow.components.workflow_monitor import WorkflowMonitor
from core.workflow.models.context import ResearchWorkflowContext, WorkflowStage


def test_workflow_monitor_tracking():
    monitor = WorkflowMonitor()
    ctx = ResearchWorkflowContext()

    monitor.record_stage_start(ctx, WorkflowStage.GOAL_ANALYZED)
    latency = monitor.record_stage_complete(ctx, WorkflowStage.GOAL_ANALYZED)

    audit = monitor.audit_status(ctx)

    assert audit["current_stage"] == "goal_analyzed"
    assert audit["latency_ms"] >= 0.0
    assert latency >= 0.0
