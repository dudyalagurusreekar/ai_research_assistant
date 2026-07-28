import logging
from typing import Any, Optional

logger = logging.getLogger("ExecutionController")

class BudgetExceededError(Exception):
    """Raised when an execution budget (steps, tokens) is exceeded."""

class LoopDetectedError(Exception):
    """Raised when an infinite loop of repeating actions/failures is detected."""


class ExecutionController:
    """Monitors and enforces execution boundaries for the Browser Planner."""

    def __init__(
        self,
        max_actions: int = 15,
        max_tokens: int = 150000,
        max_consecutive_failures: int = 3
    ) -> None:
        """Initialize the Execution Controller.

        Args:
            max_actions: Maximum allowed browser actions before aborting.
            max_tokens: Cumulative total token limit for the session.
            max_consecutive_failures: Max allowed consecutive action failures.
        """
        self.max_actions = max_actions
        self.max_tokens = max_tokens
        self.max_consecutive_failures = max_consecutive_failures

        self.current_action_count = 0
        self.total_tokens_used = 0
        self.consecutive_failures = 0
        self.last_failed_action: Optional[str] = None
        self._logger = logger

    def estimate_budget(self, goal: str) -> int:
        """Dynamically calculates step budget based on task instructions.

        Args:
            goal (str): Natural language goal description.

        Returns:
            int: Calculated dynamic steps budget.
        """
        goal_lower = goal.lower()
        complex_keywords = [
            "extract", "scrape", "search", "wikipedia", "screenshot", 
            "verify", "login", "report", "fill", "form", "all", 
            "each", "every", "multiple", "table", "csv", "json"
        ]
        
        # Base steps
        steps = 10
        
        # Adjust based on keywords
        for kw in complex_keywords:
            if kw in goal_lower:
                steps += 3
                
        # Limit between 10 and 25
        return max(10, min(steps, 25))

    def record_action(self) -> None:
        """Increment action counter and check against max_actions budget."""
        self.current_action_count += 1
        if self.current_action_count > self.max_actions:
            raise BudgetExceededError(
                f"Action budget exceeded: reached {self.current_action_count} / {self.max_actions} actions."
            )

    def record_token_usage(self, usage_metadata: Optional[Any]) -> None:
        """Extract and accumulate token usage from LLM response metadata."""
        if not usage_metadata:
            return

        tokens_added = 0
        if hasattr(usage_metadata, "total_tokens"):
            tokens_added = getattr(usage_metadata, "total_tokens", 0) or 0
        elif isinstance(usage_metadata, dict):
            tokens_added = usage_metadata.get("total_tokens", 0) or 0

        # Guard against mock objects in unit testing
        if not isinstance(tokens_added, (int, float)):
            tokens_added = 0

        self.total_tokens_used += tokens_added
        if self.total_tokens_used > self.max_tokens:
            raise BudgetExceededError(
                f"Token budget exceeded: used {self.total_tokens_used} / {self.max_tokens} tokens."
            )

    def check_loop(self, action_signature: str, success: bool) -> None:
        """Monitor action outcomes to detect repeating failure loops.

        Args:
            action_signature: String identifier of action, target, and arguments.
            success: Outcome of the action execution.
        """
        if not success:
            if self.last_failed_action == action_signature:
                self.consecutive_failures += 1
            else:
                self.last_failed_action = action_signature
                self.consecutive_failures = 1
        else:
            self.last_failed_action = None
            self.consecutive_failures = 0

        if self.consecutive_failures >= self.max_consecutive_failures:
            raise LoopDetectedError(
                f"Loop detected: Action '{action_signature}' failed {self.consecutive_failures} consecutive times."
            )

    def should_replan(self) -> bool:
        """Evaluates whether consecutive failures indicate a need to replan."""
        return self.consecutive_failures >= (self.max_consecutive_failures - 1)
