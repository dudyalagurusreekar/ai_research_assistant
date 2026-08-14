"""Integration test for LearningWorkflowIntegration."""

import pytest

from core.workflow.integration import LearningWorkflowIntegration
from core.workflow.models.context import ResearchWorkflowContext
from core.workflow.models.goal import ResearchGoal


def test_learning_workflow_integration():
    integration = LearningWorkflowIntegration()
    ctx = ResearchWorkflowContext()
    ctx.goal = ResearchGoal(raw_query="Optimize Workflow Strategies")

    integration.record_workflow_experience(ctx)
    assert True  # Successfully recorded without exception
