"""Action Verification Engine (`tools/browser/verification/engine.py`).

Dedicated validation subsystem that decouples action execution from verification.
Provides clear checks for URL matching, DOM mutations, expected elements,
text presence, and file downloads.
"""

import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional
import logging

logger = logging.getLogger("ActionVerificationEngine")


class VerificationType(Enum):
    """Types of verification checks."""

    URL = "url"
    DOM_CHANGE = "dom_change"
    ELEMENT_PRESENT = "element_present"
    TEXT_PRESENT = "text_present"
    DOWNLOAD = "download"
    ACTION_SUCCESS = "action_success"


@dataclass
class VerificationResult:
    """Outcome of a verification check."""

    passed: bool
    verification_type: VerificationType
    details: str
    actual_value: Optional[Any] = None
    expected_value: Optional[Any] = None


class ActionVerificationEngine:
    """Stateless verification engine for validating browser actions and state changes."""

    def __init__(self) -> None:
        self._logger = logger

    def verify_url(self, expected_pattern: str, current_url: str) -> VerificationResult:
        """Verify that current_url matches an expected substring or regex pattern."""
        if not current_url:
            return VerificationResult(
                passed=False,
                verification_type=VerificationType.URL,
                details="Current URL is empty.",
                actual_value="",
                expected_value=expected_pattern,
            )

        passed = expected_pattern in current_url or bool(
            re.search(expected_pattern, current_url, re.IGNORECASE)
        )
        return VerificationResult(
            passed=passed,
            verification_type=VerificationType.URL,
            details=f"URL '{current_url}' {'matches' if passed else 'does not match'} '{expected_pattern}'.",
            actual_value=current_url,
            expected_value=expected_pattern,
        )

    def verify_dom_change(self, old_hash: Optional[str], new_hash: Optional[str]) -> VerificationResult:
        """Verify that a DOM mutation occurred between actions."""
        passed = (old_hash != new_hash) and (new_hash is not None)
        return VerificationResult(
            passed=passed,
            verification_type=VerificationType.DOM_CHANGE,
            details="DOM mutated as expected." if passed else "DOM hash remained identical; no mutation detected.",
            actual_value=new_hash,
            expected_value=old_hash,
        )

    def verify_element_present(self, selector: str, html_or_pruned_dom: str) -> VerificationResult:
        """Verify that a specific element or selector string appears in the DOM representation."""
        if not html_or_pruned_dom:
            return VerificationResult(
                passed=False,
                verification_type=VerificationType.ELEMENT_PRESENT,
                details="Page content is empty.",
                actual_value=None,
                expected_value=selector,
            )

        s_lower = selector.lower().strip()
        dom_lower = html_or_pruned_dom.lower()

        passed = s_lower in dom_lower
        if not passed and s_lower.startswith("#"):
            passed = f'id="{s_lower[1:]}"' in dom_lower or f"id='{s_lower[1:]}'" in dom_lower or f"#{s_lower[1:]}" in dom_lower
        elif not passed and s_lower.startswith("."):
            passed = f'class="{s_lower[1:]}"' in dom_lower or f"class='{s_lower[1:]}'" in dom_lower

        return VerificationResult(
            passed=passed,
            verification_type=VerificationType.ELEMENT_PRESENT,
            details=f"Element '{selector}' {'found' if passed else 'not found'} in page content.",
            actual_value=selector if passed else None,
            expected_value=selector,
        )

    def verify_text_present(self, expected_text: str, page_text: str) -> VerificationResult:
        """Verify that expected text substring appears in page text."""
        if not page_text:
            return VerificationResult(
                passed=False,
                verification_type=VerificationType.TEXT_PRESENT,
                details="Page text is empty.",
                actual_value="",
                expected_value=expected_text,
            )

        passed = expected_text.lower() in page_text.lower()
        return VerificationResult(
            passed=passed,
            verification_type=VerificationType.TEXT_PRESENT,
            details=f"Text '{expected_text}' {'present' if passed else 'missing'} on page.",
            actual_value=expected_text if passed else None,
            expected_value=expected_text,
        )

    def verify_download(
        self,
        file_path: str,
        min_size_bytes: int = 1,
    ) -> VerificationResult:
        """Verify that a file was downloaded and exists on disk with valid size."""
        exists = os.path.exists(file_path)
        actual_size = os.path.getsize(file_path) if exists else 0
        passed = exists and actual_size >= min_size_bytes

        return VerificationResult(
            passed=passed,
            verification_type=VerificationType.DOWNLOAD,
            details=f"Download '{file_path}' {'verified' if passed else 'failed'} (size: {actual_size} bytes).",
            actual_value=actual_size,
            expected_value=min_size_bytes,
        )
