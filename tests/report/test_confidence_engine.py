"""Tests for ConfidenceEngine."""
from tools.report.validator.confidence_engine import ConfidenceEngine
from tools.report.validator.self_verification import VerificationResult

def test_confidence_engine_high_confidence():
    engine = ConfidenceEngine()
    verification = VerificationResult(is_valid=True)
    evidence = ["doc1", "doc2"]
    
    res = engine.calculate_confidence("Valid text [1].", evidence, verification)
    assert res["score"] == 1.0
    assert "High confidence" in str(res["explanations"])

def test_confidence_engine_no_evidence():
    engine = ConfidenceEngine()
    verification = VerificationResult(is_valid=True)
    
    res = engine.calculate_confidence("Text without evidence.", [], verification)
    assert res["score"] == 0.6
    assert "No direct evidence" in str(res["uncertainties"])

def test_confidence_engine_invalid_verification():
    engine = ConfidenceEngine()
    verification = VerificationResult(is_valid=False)
    verification.issues.append("Missing citation")
    verification.unsupported_claims.append("Claim 1")
    
    res = engine.calculate_confidence("Invalid text.", ["doc1"], verification)
    # 1.0 - 0.2 (1 issue) - 0.3 (unsupported) = 0.5
    assert res["score"] == 0.5
    assert "Low confidence" in str(res["explanations"]) or "Moderate confidence" in str(res["explanations"])
