"""Browser Action Verifier for post-execution state validation."""

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class BrowserVerificationResult:
    """Outcome of a browser verification check."""

    passed: bool
    check_type: str
    details: str

    @property
    def verification_type(self) -> Any:
        try:
            from tools.browser.verification import VerificationType
            return VerificationType(self.check_type)
        except Exception:
            return self.check_type


class BrowserActionVerifier:
    """Validates URL matches, DOM mutations, element presence, and file download completion."""

    def verify_url(self, expected_pattern: str, current_url: str) -> BrowserVerificationResult:
        """Verify current URL contains or matches expected pattern."""
        passed = expected_pattern.lower() in current_url.lower()
        return BrowserVerificationResult(
            passed=passed,
            check_type="url",
            details=f"URL '{current_url}' {'matches' if passed else 'does not match'} '{expected_pattern}'.",
        )

    def verify_dom_mutation(self, old_hash: str, new_hash: str) -> BrowserVerificationResult:
        """Verify DOM hash mutated after an interactive action."""
        passed = (old_hash != new_hash) and bool(new_hash)
        return BrowserVerificationResult(
            passed=passed,
            check_type="dom_mutation",
            details="DOM mutated successfully." if passed else "DOM hash remained unchanged.",
        )

    def verify_dom_change(self, old_hash: str, new_hash: str) -> BrowserVerificationResult:
        """Alias for verify_dom_mutation."""
        return self.verify_dom_mutation(old_hash, new_hash)

    def verify_element_present(self, selector: str, page_content: str) -> BrowserVerificationResult:
        """Verify element selector or text is present in page content."""
        s_clean = selector.lower().replace("#", "").replace(".", "")
        passed = s_clean in page_content.lower()
        return BrowserVerificationResult(
            passed=passed,
            check_type="element_presence",
            details=f"Element '{selector}' {'found' if passed else 'missing'} in content.",
        )

    def verify_text_present(self, text: str, page_content: str) -> BrowserVerificationResult:
        """Verify text snippet is present in page content."""
        passed = text.lower() in page_content.lower()
        return BrowserVerificationResult(
            passed=passed,
            check_type="text_presence",
            details=f"Text '{text}' {'found' if passed else 'missing'} in content.",
        )

    def verify_download(self, file_path: str, min_bytes: int = 1) -> BrowserVerificationResult:
        """Verify file exists on disk with minimum size."""
        exists = os.path.exists(file_path)
        actual_bytes = os.path.getsize(file_path) if exists else 0
        passed = exists and actual_bytes >= min_bytes
        return BrowserVerificationResult(
            passed=passed,
            check_type="download",
            details=f"File '{file_path}' {'verified' if passed else 'missing/empty'} (Size: {actual_bytes}B).",
        )
