"""Recovery Engine Proxy.

Maintains backward-compatibility for direct imports of RecoveryEngine from tools.browser.recovery.
"""

from tools.browser.recovery.base import RecoveryResult
from tools.browser.recovery.classifier import ErrorCategory, ErrorClassifier
from tools.browser.recovery.engine import RecoveryEngine, RecoveryMetrics, RecoveryPolicyEngine

__all__ = [
    "RecoveryEngine",
    "RecoveryResult",
    "ErrorCategory",
    "ErrorClassifier",
    "RecoveryMetrics",
    "RecoveryPolicyEngine",
]
