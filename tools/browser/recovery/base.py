"""Base classes, context, and result structures for the browser self-healing system.

Defines custom exceptions, shared execution contexts, and abstract recovery
strategy classes.
"""

import abc
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from tools.browser.core.browser import Browser
from tools.browser.models.response import ActionResult

logger = logging.getLogger("RecoveryEngine.Base")


class RecoveryError(Exception):
    """Base class for all recovery engine errors."""
    pass


class RecoveryStrategyError(RecoveryError):
    """Raised when a specific recovery strategy encounters an internal error."""
    pass


class SessionRestorationError(RecoveryError):
    """Raised when browser session/context restoration fails during crash recovery."""
    pass


@dataclass
class RecoveryResult:
    """Outcome of a single recovery strategy execution.

    Attributes:
        success: Whether the recovery attempt successfully self-healed the issue.
        strategy_used: Name of the strategy class executed.
        attempts: Number of sub-attempts performed.
        message: Informational message describing the result.
        action_result: The new successful ActionResult, if recovered.
        discovered_alternative_selector: Optional CSS selector, if discovered.
    """

    success: bool
    strategy_used: str = ""
    attempts: int = 0
    message: str = ""
    action_result: Optional[ActionResult] = None
    discovered_alternative_selector: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert recovery result to JSON-compatible dictionary."""
        return {
            "success": self.success,
            "strategy_used": self.strategy_used,
            "attempts": self.attempts,
            "message": self.message,
            "discovered_alternative_selector": self.discovered_alternative_selector,
        }


# Forward declare enum to prevent circular imports
class ErrorCategory:
    pass


@dataclass
class RecoveryContext:
    """Context passed to recovery strategies to attempt self-healing.

    Attributes:
        browser: The Browser facade instance.
        action_dict: The action dictionary that failed.
        failed_result: The ActionResult output of the failure.
        error_category: Classified category of the error.
        error_message: Raw string message of the failure.
        attempt_number: Incremental attempt counter.
        metadata: Optional dictionary for tracking execution context parameters.
    """

    browser: Browser
    action_dict: Dict[str, Any]
    failed_result: ActionResult
    error_category: Any  # Actually ErrorCategory
    error_message: str
    attempt_number: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseRecoveryStrategy(abc.ABC):
    """Abstract base class for all browser self-healing strategies."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """String identifier of the recovery strategy."""
        pass

    @abc.abstractmethod
    def attempt(self, ctx: RecoveryContext) -> RecoveryResult:
        """Attempt to recover from the failure described in the context.

        Args:
            ctx: RecoveryContext structure.

        Returns:
            RecoveryResult: Details of the self-healing outcome.

        Raises:
            RecoveryStrategyError: If execution encounters unrecoverable errors.
        """
        pass
