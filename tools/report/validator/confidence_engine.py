"""Confidence Engine calculating evidence-based confidence scores and uncertainties."""

from typing import Dict, Any, List
from infrastructure.logging.logger import StructuredLogger
from tools.report.validator.self_verification import VerificationResult


class ConfidenceEngine:
    """Calculates a confidence score and identifies uncertainties for draft answers."""

    def __init__(self):
        self._logger = StructuredLogger("ConfidenceEngine")

    def calculate_confidence(self, draft_text: str, evidence: List[Any], verification_result: VerificationResult) -> Dict[str, Any]:
        """Generate a confidence score (0.0 to 1.0) with an explanation."""
        score = 1.0
        explanations = []
        uncertainties = []

        if not draft_text:
            return {"score": 0.0, "explanations": ["Empty text"], "uncertainties": ["No content provided."]}

        if not evidence:
            score -= 0.4
            uncertainties.append("No direct evidence was provided to support the text.")
        else:
            explanations.append(f"Text is supported by {len(evidence)} pieces of evidence.")

        if not verification_result.is_valid:
            score -= 0.2 * len(verification_result.issues)
            uncertainties.extend(verification_result.issues)

        if verification_result.unsupported_claims:
            score -= 0.3
            uncertainties.append("Contains unsupported claims.")

        if verification_result.missing_citations:
            score -= 0.1
            explanations.append("Lacks strict citations for some facts.")

        score = max(0.0, min(1.0, score))

        if score > 0.8:
            explanations.append("High confidence in the draft's accuracy and foundation.")
        elif score > 0.5:
            explanations.append("Moderate confidence; some claims may lack strong evidence.")
        else:
            explanations.append("Low confidence; significant uncertainties or missing evidence.")

        result = {
            "score": round(score, 2),
            "explanations": explanations,
            "uncertainties": uncertainties
        }

        self._logger.info(
            f"Calculated confidence score: {result['score']}",
            extra_fields={"confidence": result}
        )

        return result
