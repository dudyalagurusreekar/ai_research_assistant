"""Integration test for CollaborationWorkflowIntegration."""

import pytest

from core.collaboration.models.agent_info import AgentRole
from core.collaboration.models.context import TaskAssignment
from core.workflow.integration import CollaborationWorkflowIntegration


def test_collaboration_workflow_integration():
    integration = CollaborationWorkflowIntegration()
    assignments = [
        TaskAssignment(
            task_id="t_1",
            title="Literature Task",
            description="Perform literature survey",
            target_role=AgentRole.RESEARCH,
        )
    ]

    collab_ctx = integration.dispatch_research_wave(assignments, query="Quantum Benchmark")
    assert collab_ctx is not None
    assert collab_ctx.metrics.completed_tasks == 1
