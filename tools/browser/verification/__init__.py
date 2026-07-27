"""Browser Verification package."""

from enum import Enum
from tools.browser.verification.verifier import BrowserActionVerifier, BrowserVerificationResult


class VerificationType(Enum):
    URL = "url"
    DOM_MUTATION = "dom_mutation"
    ELEMENT_PRESENCE = "element_presence"
    TEXT_PRESENCE = "text_presence"
    DOWNLOAD = "download"


# Alias for backward compatibility across test suites
ActionVerificationEngine = BrowserActionVerifier

__all__ = [
    "BrowserActionVerifier",
    "BrowserVerificationResult",
    "ActionVerificationEngine",
    "VerificationType",
]
