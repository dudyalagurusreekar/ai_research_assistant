"""Tests for SelfVerificationEngine."""
from tools.report.validator.self_verification import SelfVerificationEngine

def test_verify_empty_text():
    engine = SelfVerificationEngine()
    result = engine.verify("", context={})
    assert result.is_valid is False
    assert "Draft text is empty." in result.issues

def test_missing_citations():
    engine = SelfVerificationEngine()
    draft = "According to recent studies, 50% of users prefer dark mode."
    result = engine.verify(draft, context={"evidence": ["Some evidence"]})
    assert result.is_valid is False
    assert any("Potential missing citations" in issue for issue in result.issues)
    assert len(result.missing_citations) == 1

def test_unsupported_claims():
    engine = SelfVerificationEngine()
    draft = "This is a very long assertion that goes on and on. " * 10
    result = engine.verify(draft, context={})
    assert result.is_valid is False
    assert result.requires_more_search is True
    assert len(result.unsupported_claims) == 1

def test_valid_text():
    engine = SelfVerificationEngine()
    draft = "This is a valid claim [1]."
    result = engine.verify(draft, context={"evidence": [{"title": "Doc 1"}]})
    assert result.is_valid is True
    assert len(result.issues) == 0
