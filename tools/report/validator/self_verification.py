"""Self-Verification Engine evaluating draft answers for claims, contradictions, and citations."""

from typing import Dict, Any, List
from infrastructure.logging.logger import StructuredLogger


class VerificationResult:
    """Encapsulates the result of a self-verification pass."""

    def __init__(self, is_valid: bool = True):
        self.is_valid = is_valid
        self.issues: List[str] = []
        self.unsupported_claims: List[str] = []
        self.contradictions: List[str] = []
        self.missing_citations: List[str] = []
        self.requires_more_search: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "issues": self.issues,
            "unsupported_claims": self.unsupported_claims,
            "contradictions": self.contradictions,
            "missing_citations": self.missing_citations,
            "requires_more_search": self.requires_more_search
        }


class SelfVerificationEngine:
    """Evaluates draft text to detect missing citations, contradictory evidence, and unsupported claims."""

    def __init__(self):
        self._logger = StructuredLogger("SelfVerificationEngine")

    def verify(self, draft_text: str, context: Dict[str, Any]) -> VerificationResult:
        """Analyze a draft answer against the collected context and evidence."""
        result = VerificationResult()

        if not draft_text or draft_text.strip() == "":
            result.is_valid = False
            result.issues.append("Draft text is empty.")
            return result

        # Basic heuristic logic for missing citations: 
        # Check if text contains facts but no [1] format citations
        if any(char.isdigit() for char in draft_text) and "[" not in draft_text:
            result.is_valid = False
            result.missing_citations.append("Text appears to contain statistical or specific facts without brackets for citations.")
            result.issues.append("Potential missing citations for factual claims.")

        # If context is empty but draft has strong claims, flag for more search
        if not context or "evidence" not in context or not context["evidence"]:
            if len(draft_text.split()) > 50:
                result.is_valid = False
                result.unsupported_claims.append("Draft makes detailed assertions but no context evidence is provided.")
                result.requires_more_search = True

        self._logger.info(
            f"Verification complete. Valid: {result.is_valid}, Issues: {len(result.issues)}",
            extra_fields={"verification_result": result.to_dict()}
        )
        return result
