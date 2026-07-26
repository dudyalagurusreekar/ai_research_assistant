"""Action Verification package (`tools/browser/verification/`).

Exposes ActionVerificationEngine for decoupling execution from validation.
"""

from tools.browser.verification.engine import (
    ActionVerificationEngine,
    VerificationResult,
    VerificationType,
)

__all__ = [
    "ActionVerificationEngine",
    "VerificationResult",
    "VerificationType",
]
