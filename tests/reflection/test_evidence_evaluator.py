"""Tests for EvidenceEvaluator."""

import pytest
from core.reflection.components.evidence_evaluator import EvidenceEvaluator
from core.reflection.models.reflection import EvidenceQuality


class TestEvidenceEvaluator:
    def setup_method(self):
        self.evaluator = EvidenceEvaluator()

    def test_evaluate_empty(self):
        assess = self.evaluator.evaluate({})
        assert assess.quality == EvidenceQuality.INSUFFICIENT
        assert assess.quality_score == 0.0

    def test_evaluate_high_quality_diverse(self):
        outputs = {
            "search_tool": "Deep web search results for quantum computing.",
            "document_tool": "Parsed PDF document content describing quantum algorithms.",
            "browser_tool": "Webpage content detailing quantum supremacy benchmarks.",
        }
        assess = self.evaluator.evaluate(outputs)
        assert assess.quality == EvidenceQuality.HIGH
        assert assess.source_count == 3
        assert assess.conflict_detected is False

    def test_evaluate_detects_conflict(self):
        outputs = {
            "search_tool": "Source A states CRISPR was invented in 2012.",
            "browser_tool": "Source B claims CRISPR was invented in 2023, contrary to prior claims. Conflict exists.",
        }
        assess = self.evaluator.evaluate(outputs)
        assert assess.conflict_detected is True
        assert assess.quality == EvidenceQuality.CONFLICTING
        assert len(assess.conflicting_sources) >= 1
