"""Recovery Engine Coordinator.

Orchestrates error classification, maps failures to policy chains, manages retry
budgets, executes recovery strategies, and collects operational metrics.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from tools.browser.core.browser import Browser
from tools.browser.models.response import ActionResult
from tools.browser.recovery.base import (
    BaseRecoveryStrategy,
    RecoveryContext,
    RecoveryResult,
)
from tools.browser.recovery.classifier import ErrorCategory, ErrorClassifier
from tools.browser.recovery.strategies import (
    AlternativeSelectorDiscovery,
    BrowserCrashRecovery,
    DismissOverlay,
    NetworkInterruptionRecovery,
    PageReload,
    PlannerFeedbackStrategy,
    RetryWithBackoff,
    ScrollIntoView,
    SessionRefresh,
    WaitForDOMStability,
    CaptchaRecoveryStrategy,
)

logger = logging.getLogger("RecoveryEngine.Engine")


class RecoveryMetrics:
    """Tracks self-healing metrics and recovery history for observability."""

    def __init__(self) -> None:
        self.total_attempts: int = 0
        self.total_successes: int = 0
        self.total_failures: int = 0
        self.total_recovery_time_ms: float = 0.0
        self.by_category: Dict[str, Dict[str, int]] = {}
        self.by_strategy: Dict[str, Dict[str, int]] = {}
        self.history: List[Dict[str, Any]] = []

    def record_attempt(
        self,
        category: ErrorCategory,
        strategy_name: str,
        success: bool,
        duration_ms: float,
        message: str = "",
    ) -> None:
        """Record the outcome of a single strategy recovery attempt.

        Args:
            category: Error taxonomy category.
            strategy_name: Name of strategy executed.
            success: Whether strategy succeeded.
            duration_ms: Duration in milliseconds.
            message: Informational details.
        """
        self.total_attempts += 1
        self.total_recovery_time_ms += duration_ms

        if success:
            self.total_successes += 1
        else:
            self.total_failures += 1

        # Track by Category
        cat_str = category.value
        if cat_str not in self.by_category:
            self.by_category[cat_str] = {"attempts": 0, "successes": 0, "failures": 0}
        self.by_category[cat_str]["attempts"] += 1
        if success:
            self.by_category[cat_str]["successes"] += 1
        else:
            self.by_category[cat_str]["failures"] += 1

        # Track by Strategy
        if strategy_name not in self.by_strategy:
            self.by_strategy[strategy_name] = {"attempts": 0, "successes": 0, "failures": 0}
        self.by_strategy[strategy_name]["attempts"] += 1
        if success:
            self.by_strategy[strategy_name]["successes"] += 1
        else:
            self.by_strategy[strategy_name]["failures"] += 1

        # Log history item
        self.history.append({
            "timestamp": time.time(),
            "category": cat_str,
            "strategy": strategy_name,
            "success": success,
            "duration_ms": duration_ms,
            "message": message,
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_attempts": self.total_attempts,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "success_rate_pct": (
                (self.total_successes / self.total_attempts * 100.0)
                if self.total_attempts > 0
                else 0.0
            ),
            "avg_recovery_time_ms": (
                (self.total_recovery_time_ms / self.total_attempts)
                if self.total_attempts > 0
                else 0.0
            ),
            "by_category": self.by_category,
            "by_strategy": self.by_strategy,
        }


# Default strategy chains per error category
_DEFAULT_RECOVERY_POLICIES: Dict[ErrorCategory, List[BaseRecoveryStrategy]] = {
    ErrorCategory.ELEMENT_NOT_FOUND: [
        WaitForDOMStability(),
        AlternativeSelectorDiscovery(),
        RetryWithBackoff(),
    ],
    ErrorCategory.ELEMENT_NOT_INTERACTABLE: [
        DismissOverlay(),
        ScrollIntoView(),
        WaitForDOMStability(),
        RetryWithBackoff(),
    ],
    ErrorCategory.STALE_ELEMENT: [
        WaitForDOMStability(),
        AlternativeSelectorDiscovery(),
        RetryWithBackoff(),
    ],
    ErrorCategory.BROWSER_CRASH: [
        BrowserCrashRecovery(),
    ],
    ErrorCategory.NETWORK_ERROR: [
        NetworkInterruptionRecovery(),
        RetryWithBackoff(),
    ],
    ErrorCategory.NAVIGATION_FAILURE: [
        RetryWithBackoff(),
        PageReload(),
    ],
    ErrorCategory.TIMEOUT: [
        RetryWithBackoff(base_delay_s=1.0),
        PageReload(),
    ],
    ErrorCategory.DIALOG_BLOCKING: [
        DismissOverlay(),
        RetryWithBackoff(),
    ],
    ErrorCategory.JS_EXCEPTION: [
        RetryWithBackoff(),
    ],
    ErrorCategory.AUTH_INTERRUPTION: [
        SessionRefresh(),
    ],
    ErrorCategory.SESSION_EXPIRED: [
        SessionRefresh(),
        PageReload(),
    ],
    ErrorCategory.CAPTCHA_INTERRUPTION: [
        CaptchaRecoveryStrategy(),
        RetryWithBackoff(base_delay_s=2.0),
    ],
    ErrorCategory.UNKNOWN: [
        RetryWithBackoff(),
    ],
}


class RecoveryPolicyEngine:
    """Manages mapping between ErrorCategory failure modes and recovery strategy chains."""

    def __init__(
        self, policies: Optional[Dict[ErrorCategory, List[BaseRecoveryStrategy]]] = None
    ) -> None:
        """Initialize the policy engine with mapping strategies.

        Args:
            policies: Map of ErrorCategory to List of strategies.
                Defaults to _DEFAULT_RECOVERY_POLICIES if None.
        """
        self.policies = policies or dict(_DEFAULT_RECOVERY_POLICIES)

    def get_strategies(self, category: ErrorCategory) -> List[BaseRecoveryStrategy]:
        """Fetch the list of strategies registered for a category.

        Args:
            category: Error category.

        Returns:
            List[BaseRecoveryStrategy]: Strategy chain.
        """
        return self.policies.get(category, self.policies.get(ErrorCategory.UNKNOWN, []))

    def set_policy(self, category: ErrorCategory, strategies: List[BaseRecoveryStrategy]) -> None:
        """Overwrite the strategy chain for a specific error category.

        Args:
            category: Target error category.
            strategies: New strategy list to map.
        """
        self.policies[category] = strategies


class RecoveryEngine:
    """Enterprise-grade Recovery Engine coordinating self-healing lifecycle.

    Attributes:
        browser: Reference to the Browser facade.
        policy_engine: Active RecoveryPolicyEngine configuration.
        max_recovery_attempts: Retry budget constraint.
        metrics: Active statistics container.
    """

    def __init__(
        self,
        browser: Browser,
        policy_engine: Optional[RecoveryPolicyEngine] = None,
        max_recovery_attempts: int = 3,
    ) -> None:
        """Initialize the Recovery Engine.

        Args:
            browser: The active Browser facade.
            policy_engine: The recovery policy mapping engine.
            max_recovery_attempts: Max strategy attempts per error occurrence.
        """
        self.browser = browser
        self.policy_engine = policy_engine or RecoveryPolicyEngine()
        self.max_recovery_attempts = max_recovery_attempts
        self.metrics = RecoveryMetrics()
        self._logger = logger

    def attempt_recovery(
        self,
        action_dict: Dict[str, Any],
        failed_result: ActionResult,
        exception: Optional[Exception] = None,
        memory_manager: Optional[Any] = None,
    ) -> RecoveryResult:
        """Determine and run recovery strategies for a failed action.

        Args:
            action_dict: Action parameters.
            failed_result: Action result indicating failure.
            exception: Optional Exception class.
            memory_manager: Optional MemoryManager facade.

        Returns:
            RecoveryResult: The self-healing outcome.
        """
        error_msg = "; ".join(failed_result.errors) if failed_result.errors else str(exception or "")
        category = ErrorClassifier.classify(error_msg, exception)
        strategies = self.policy_engine.get_strategies(category)

        self._logger.info(
            f"Recovery Engine triggered: Category={category.value}, "
            f"Action={action_dict.get('action')}, "
            f"Selector={action_dict.get('selector')}"
        )

        if not strategies:
            self._logger.warning(f"No strategies configured for error category '{category.value}'.")
            return RecoveryResult(
                success=False,
                message=f"No strategies configured for category {category.value}",
            )

        # Setup Recovery Context
        ctx = RecoveryContext(
            browser=self.browser,
            action_dict=action_dict,
            failed_result=failed_result,
            error_category=category,
            error_message=error_msg,
        )

        total_attempts = 0

        # Execute each strategy in the chain up to max_recovery_attempts
        for strategy in strategies:
            if total_attempts >= self.max_recovery_attempts:
                self._logger.warning("Recovery budget limit reached. Stopping recovery chain.")
                break

            total_attempts += 1
            ctx.attempt_number = total_attempts
            start_time = time.time()

            self._logger.info(
                f"Executing strategy '{strategy.name}' (attempt {total_attempts}/{self.max_recovery_attempts})..."
            )

            try:
                res = strategy.attempt(ctx)
            except Exception as e:
                self._logger.error(f"Strategy '{strategy.name}' threw exception: {e}")
                res = RecoveryResult(
                    success=False,
                    strategy_used=strategy.name,
                    message=f"Strategy execution error: {e}",
                )

            duration_ms = (time.time() - start_time) * 1000.0

            # Record metrics
            self.metrics.record_attempt(
                category=category,
                strategy_name=strategy.name,
                success=res.success,
                duration_ms=duration_ms,
                message=res.message,
            )

            if res.success:
                res.attempts = total_attempts
                
                # Check for alternative selector and write it to procedural memory
                if res.discovered_alternative_selector and memory_manager:
                    try:
                        domain = getattr(
                            memory_manager.working.current_state,
                            "url",
                            action_dict.get("url", "unknown"),
                        )
                        if domain and domain != "unknown":
                            from urllib.parse import urlparse
                            domain_name = urlparse(domain).netloc or domain
                            original = action_dict.get("selector", "")
                            # Store learned alternative selector for future planner queries
                            memory_manager.procedural.store_alternative_selector(
                                domain=domain_name,
                                original_selector=original,
                                alternative_selector=res.discovered_alternative_selector,
                            )
                    except Exception as e:
                        self._logger.warning(f"Failed to store alternative selector in memory: {e}")

                return res

        # If all strategies in the chain fail, run the PlannerFeedbackStrategy
        self._logger.error(
            f"All recovery strategies exhausted for category '{category.value}'."
        )
        feedback_strategy = PlannerFeedbackStrategy()
        fallback_res = feedback_strategy.attempt(ctx)
        fallback_res.attempts = total_attempts

        return fallback_res
