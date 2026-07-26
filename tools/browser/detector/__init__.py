"""Completion Detector package exports.

Exposes the main orchestrator, context, result DTOs, strategies, and exceptions.
"""

from tools.browser.detector.base import (
    BaseCompletionStrategy,
    CompletionContext,
    CompletionDetectorError,
    CompletionState,
    CompletionStatus,
    InvalidObjectiveError,
)
from tools.browser.detector.pipeline import CompletionDetector
from tools.browser.detector.strategies import (
    ArtifactSuccessStrategy,
    ExecutionAnomalyStrategy,
    ObjectiveEvidenceStrategy,
    StateBlockedStrategy,
    UrlRedirectionStrategy,
)

__all__ = [
    # Core Structures
    "CompletionDetector",
    "CompletionContext",
    "CompletionStatus",
    "CompletionState",
    "BaseCompletionStrategy",
    # Exceptions
    "CompletionDetectorError",
    "InvalidObjectiveError",
    # Strategies
    "ObjectiveEvidenceStrategy",
    "ArtifactSuccessStrategy",
    "UrlRedirectionStrategy",
    "StateBlockedStrategy",
    "ExecutionAnomalyStrategy",
]
