"""Integration test for DataWorkflowIntegration."""

import pytest

from core.workflow.integration import DataWorkflowIntegration


def test_data_workflow_integration():
    integration = DataWorkflowIntegration()
    rows = [
        {"latency": 1.2, "accuracy": 0.95},
        {"latency": 1.8, "accuracy": 0.92},
    ]

    profile = integration.profile_research_dataset("model_benchmarks", rows)
    assert profile is not None
    assert profile.dataset_name == "model_benchmarks"
