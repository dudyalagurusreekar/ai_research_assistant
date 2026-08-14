"""Integration test for ReflectionWorkflowIntegration."""

import pytest

from core.workflow.integration import ReflectionWorkflowIntegration
from core.workflow.models.evidence import EvidenceRecord


def test_reflection_workflow_integration():
    integration = ReflectionWorkflowIntegration()
    evidence_list = [EvidenceRecord(question_id="q1", content="Empirical research fact.")]

    valid = integration.audit_research_facts(evidence_list)
    assert valid is True
