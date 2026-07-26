"""Base structures, resource categories, and exceptions for budget management.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class BudgetManagerError(Exception):
    """Base exception for all Budget Manager errors."""
    pass


class BudgetExceededError(BudgetManagerError):
    """Raised when a specific resource consumption exceeds its budget limit."""

    def __init__(self, category: str, limit: float, consumed: float) -> None:
        self.category = category
        self.limit = limit
        self.consumed = consumed
        super().__init__(
            f"Budget limit exceeded for category '{category}': "
            f"Limit {limit}, Consumed {consumed}"
        )


class ResourceCategory(str, Enum):
    """Defines categories of computational/operational resources tracked."""

    ACTIONS = "ACTIONS"              # Number of browser primitive actions
    STEPS = "STEPS"                  # Number of planner reasoning steps
    TIME = "TIME"                    # Total wall-clock execution time (seconds)
    TOKENS = "TOKENS"                # LLM input/output tokens used
    SCREENSHOTS = "SCREENSHOTS"      # Number of screenshots captured
    MACROS = "MACROS"                # Number of macro executions
    RECOVERIES = "RECOVERIES"        # Number of recovery attempts
    API_CALLS = "API_CALLS"          # Number of direct HTTP/Fetcher API requests


class BudgetStatus(str, Enum):
    """Categorized status of a specific resource budget."""

    HEALTHY = "HEALTHY"              # Under warning threshold (< 70%)
    WARNING = "WARNING"              # Approaching limit (>= 70%)
    CRITICAL = "CRITICAL"            # Nearing exhaustion (>= 90%)
    EXHAUSTED = "EXHAUSTED"          # Consumed all budget (>= 100%)


class BudgetRecommendation(str, Enum):
    """Actionable advice issued to rebalance resources or degrade gracefully."""

    CONTINUE = "CONTINUE"                        # Keep running normally
    COMPRESS_PROMPT = "COMPRESS_PROMPT"          # Token usage high - trigger prompt compression
    REPLAN_EXPLORATION = "REPLAN_EXPLORATION"    # Action/Step budget high - restrict search pathways
    DEGRADE_VISUALS = "DEGRADE_VISUALS"          # Screenshot budget high - disable overlay or screenshot capture
    SHUTDOWN = "SHUTDOWN"                        # Critical budget exhausted - graceful emergency abort


@dataclass
class BudgetLimit:
    """Resource budget boundaries and usage tracking DTO.

    Attributes:
        limit: Hard capacity limit limit.
        consumed: Cumulative resources consumed.
        reserved: Dynamically reserved capacity.
        warning_thresholds: List of ratios (e.g. [0.70, 0.90]) triggering warning states.
    """

    limit: float
    consumed: float = 0.0
    reserved: float = 0.0
    warning_thresholds: List[float] = field(default_factory=lambda: [0.70, 0.90])

    @property
    def remaining(self) -> float:
        """Remaining unconsumed capacity."""
        return max(0.0, self.limit - self.consumed - self.reserved)

    @property
    def usage_ratio(self) -> float:
        """Ratio of consumed resources compared to hard limit."""
        return (self.consumed / self.limit) if self.limit > 0.0 else 0.0

    def get_status(self) -> BudgetStatus:
        """Resolve current status based on warning thresholds."""
        ratio = self.usage_ratio
        if ratio >= 1.0:
            return BudgetStatus.EXHAUSTED
        if ratio >= self.warning_thresholds[1]:
            return BudgetStatus.CRITICAL
        if ratio >= self.warning_thresholds[0]:
            return BudgetStatus.WARNING
        return BudgetStatus.HEALTHY
