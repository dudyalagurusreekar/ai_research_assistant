"""Integration test for KnowledgeWorkflowIntegration."""

import pytest

from core.workflow.integration import KnowledgeWorkflowIntegration
from core.workflow.models.evidence import EvidenceRecord, EvidenceSourceType


def test_knowledge_workflow_integration():
    integration = KnowledgeWorkflowIntegration()
    evidence_list = [
        EvidenceRecord(
            question_id="q1",
            content="Transformer models optimize execution latency in distributed systems.",
            source_type=EvidenceSourceType.LITERATURE,
        )
    ]

    nodes_added = integration.ingest_research_evidence(evidence_list)
    assert nodes_added >= 1
