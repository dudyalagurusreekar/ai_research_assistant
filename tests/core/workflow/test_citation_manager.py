"""Unit test for CitationManager."""

import pytest

from core.workflow.components.citation_manager import CitationManager
from core.workflow.models.citation import CitationStyle
from core.workflow.models.evidence import EvidenceRecord, EvidenceSourceType


def test_citation_manager_formatting():
    manager = CitationManager()
    e1 = EvidenceRecord(
        question_id="rq_1",
        content="Evidence content",
        source_type=EvidenceSourceType.LITERATURE,
        source_name="Quantum Benchmark Paper",
        source_url="https://arxiv.org/abs/2026.01234",
    )

    citations = manager.extract_citations_from_evidence([e1])
    assert len(citations) == 1

    bib_ieee = manager.format_bibliography(citations, style=CitationStyle.IEEE)
    bib_apa = manager.format_bibliography(citations, style=CitationStyle.APA)

    assert "Quantum Benchmark Paper" in bib_ieee
    assert "2026" in bib_apa
