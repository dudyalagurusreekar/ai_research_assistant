"""Base classes, context, states, and exception types for completion detection.

Defines the core data structures and abstraction layers for task status verification.
"""

import abc
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

from tools.browser.core.browser import Browser

logger = logging.getLogger("CompletionDetector.Base")


class CompletionDetectorError(Exception):
    """Base exception for all completion detection errors."""


class InvalidObjectiveError(CompletionDetectorError):
    """Raised when the goal/objective parameter is empty or invalid."""


class CompletionState(str, Enum):
    """Represents the validation state of the task objective."""

    COMPLETED = "COMPLETED"            # Objective fully satisfied
    PARTIAL = "PARTIAL"                # Partially satisfied (e.g. part of data extracted)
    UNCERTAIN = "UNCERTAIN"            # Satisfied but requires confirmation/verification step
    BLOCKED = "BLOCKED"                # Blocked by CAPTCHA, authentication, overlays
    IMPOSSIBLE = "IMPOSSIBLE"          # Cannot be completed (e.g. 404, invalid query criteria)
    INCOMPLETE = "INCOMPLETE"          # In progress, not yet completed


@dataclass
class CompletionStatus:
    """Consolidated status returned by the completion detection engine.

    Attributes:
        state: The final categorized CompletionState value.
        confidence: Normalized confidence score from 0.0 to 1.0.
        explanation: Natural language description explaining the decision.
        evidence: Collected indicators, page logs, or artifact details.
        details: Metadata fields mapped to dictionary values.
    """

    state: CompletionState
    confidence: float
    explanation: str = ""
    evidence: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert completion status to dictionary."""
        return {
            "state": self.state.value,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "evidence": self.evidence,
            "details": self.details,
        }


@dataclass
class CompletionContext:
    """Input payload representing browser state for evaluation.

    Attributes:
        objective: The natural language objective string.
        browser: Reference to the Browser facade.
        history: Step history list of executed actions.
        extracted_artifacts: Dictionary of scraped records, downloads, or variables.
        metadata: Custom contextual properties dictionary.
    """

    objective: str
    browser: Browser
    history: List[Dict[str, Any]] = field(default_factory=list)
    extracted_artifacts: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseCompletionStrategy(abc.ABC):
    """Abstract base class for all completion evaluation strategies."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Name of the strategy."""

    @abc.abstractmethod
    def evaluate(self, ctx: CompletionContext) -> CompletionStatus:
        """Evaluate task completion status based on the current context.

        Args:
            ctx: CompletionContext object.

        Returns:
            CompletionStatus: Evaluated status and metrics.
        """
