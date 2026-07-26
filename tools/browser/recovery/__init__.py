"""Recovery and Self-Healing Engine Package.

Exposes public exception hierarchy, context, results, categories, and orchestrator engines.
"""

from tools.browser.recovery.base import (
    BaseRecoveryStrategy,
    RecoveryContext,
    RecoveryError,
    RecoveryResult,
    RecoveryStrategyError,
    SessionRestorationError,
)
from tools.browser.recovery.classifier import ErrorCategory, ErrorClassifier
from tools.browser.recovery.engine import (
    RecoveryEngine,
    RecoveryMetrics,
    RecoveryPolicyEngine,
)

__all__ = [
    # Custom Exceptions
    "RecoveryError",
    "RecoveryStrategyError",
    "SessionRestorationError",
    # Context & Result DTOs
    "RecoveryContext",
    "RecoveryResult",
    # Classifier & Taxonomy
    "ErrorCategory",
    "ErrorClassifier",
    # Engine & Metrics
    "RecoveryEngine",
    "RecoveryPolicyEngine",
    "RecoveryMetrics",
    "BaseRecoveryStrategy",
]
