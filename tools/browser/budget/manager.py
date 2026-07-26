"""Budget Manager Engine.

Maintains budget limits, processes resource consumption, supports capacity
forecasting, and issues optimization recommendations.
"""

import logging
from typing import Dict, List, Optional, Tuple

from tools.browser.budget.base import (
    BudgetExceededError,
    BudgetLimit,
    BudgetRecommendation,
    BudgetStatus,
    ResourceCategory,
)

logger = logging.getLogger("BudgetManager.Engine")


class BudgetManager:
    """Enterprise-grade Budget Manager controlling resource consumption.

    Attributes:
        limits: Registry map from ResourceCategory to BudgetLimit tracking boundaries.
    """

    def __init__(self, limits: Optional[Dict[ResourceCategory, BudgetLimit]] = None) -> None:
        """Initialize the Budget Manager.

        Args:
            limits: Pre-defined resource limits mapping. If None, default limits are initialized.
        """
        self.limits = limits or self._get_default_limits()
        self._logger = logger

    def _get_default_limits(self) -> Dict[ResourceCategory, BudgetLimit]:
        """Generate default resource limits allocations."""
        return {
            ResourceCategory.ACTIONS: BudgetLimit(limit=25.0),
            ResourceCategory.STEPS: BudgetLimit(limit=15.0),
            ResourceCategory.TIME: BudgetLimit(limit=600.0),          # 10 minutes
            ResourceCategory.TOKENS: BudgetLimit(limit=150000.0),      # 150k tokens
            ResourceCategory.SCREENSHOTS: BudgetLimit(limit=30.0),
            ResourceCategory.MACROS: BudgetLimit(limit=10.0),
            ResourceCategory.RECOVERIES: BudgetLimit(limit=5.0),
            ResourceCategory.API_CALLS: BudgetLimit(limit=100.0),
        }

    def get_limit(self, category: ResourceCategory) -> BudgetLimit:
        """Fetch the tracking BudgetLimit DTO for a category.

        Args:
            category: Target resource category.

        Returns:
            BudgetLimit: Active tracking boundaries.
        """
        if category not in self.limits:
            # Lazy initialize category if requested with unlimited value
            self.limits[category] = BudgetLimit(limit=999999.0)
        return self.limits[category]

    def consume(self, category: ResourceCategory, amount: float) -> None:
        """Record resource consumption against a budget limit.

        Args:
            category: Target resource category.
            amount: Quantity consumed.

        Raises:
            BudgetExceededError: If the limit is exceeded.
        """
        budget = self.get_limit(category)
        new_consumed = budget.consumed + amount

        self._logger.debug(
            f"Consuming '{category.value}': current={budget.consumed:.2f}, "
            f"added={amount:.2f}, new={new_consumed:.2f}, limit={budget.limit:.2f}"
        )

        if new_consumed > budget.limit:
            # Overwrite to limit to represent exhaustion exactly
            budget.consumed = budget.limit
            raise BudgetExceededError(category.value, budget.limit, new_consumed)

        budget.consumed = new_consumed

        # Trigger logs on transitions
        status = budget.get_status()
        if status in [BudgetStatus.WARNING, BudgetStatus.CRITICAL]:
            self._logger.warning(
                f"Resource budget '{category.value}' status shifted to {status.value}! "
                f"Usage: {budget.usage_ratio:.1%}"
            )

    def reserve(self, category: ResourceCategory, amount: float) -> None:
        """Temporarily reserve resource capacity.

        Args:
            category: Target resource category.
            amount: Quantity to reserve.

        Raises:
            BudgetExceededError: If reservation exceeds remaining capacity.
        """
        budget = self.get_limit(category)
        if amount > budget.remaining:
            raise BudgetExceededError(
                f"{category.value} (Reservation)",
                budget.limit,
                budget.consumed + budget.reserved + amount,
            )
        budget.reserved += amount

    def release(self, category: ResourceCategory, amount: float) -> None:
        """Free previously reserved resource capacity.

        Args:
            category: Target resource category.
            amount: Quantity to release.
        """
        budget = self.get_limit(category)
        budget.reserved = max(0.0, budget.reserved - amount)

    def rebalance(self, source: ResourceCategory, target: ResourceCategory, amount: float) -> None:
        """Transfer allocated budget limits between categories.

        Args:
            source: Source resource category.
            target: Target resource category.
            amount: Quantity of limit to transfer.
        """
        src_budget = self.get_limit(source)
        tgt_budget = self.get_limit(target)

        # Allow rebalancing only if source has enough remaining capacity in its limit
        transferable = src_budget.limit - src_budget.consumed - src_budget.reserved
        actual_transfer = min(amount, transferable)

        if actual_transfer > 0:
            src_budget.limit -= actual_transfer
            tgt_budget.limit += actual_transfer
            self._logger.info(
                f"Rebalanced limits: Transferred {actual_transfer:.2f} limit units "
                f"from '{source.value}' to '{target.value}'."
            )

    def forecast_capacity(self, category: ResourceCategory, rate_per_step: float) -> float:
        """Forecast remaining execution steps before budget exhaustion.

        Args:
            category: Target resource category.
            rate_per_step: Historical resource consumption rate per reasoning step.

        Returns:
            float: Number of steps remaining. Returns 999.0 if rate is <= 0.
        """
        if rate_per_step <= 0.0:
            return 999.0
        budget = self.get_limit(category)
        remaining_capacity = budget.limit - budget.consumed - budget.reserved
        return max(0.0, remaining_capacity / rate_per_step)

    def get_recommendation(self) -> Tuple[BudgetRecommendation, str]:
        """Aggregate statuses of all categories and return advisory recommendations.

        Returns:
            Tuple[BudgetRecommendation, str]: Recommended escape action and explanation.
        """
        statuses = {cat: limit.get_status() for cat, limit in self.limits.items()}

        # 1. Exhaustion triggers immediate shutdown
        exhausted_cats = [cat.value for cat, stat in statuses.items() if stat == BudgetStatus.EXHAUSTED]
        if exhausted_cats:
            return (
                BudgetRecommendation.SHUTDOWN,
                f"Emergency Shutdown: Resource budgets exhausted for: {exhausted_cats}",
            )

        # 2. Critical boundaries triggers replanning
        critical_cats = [cat.value for cat, stat in statuses.items() if stat == BudgetStatus.CRITICAL]
        if any(c in critical_cats for c in ["ACTIONS", "STEPS"]):
            return (
                BudgetRecommendation.REPLAN_EXPLORATION,
                "Restricting exploration: Action or Step steps budget in critical state.",
            )

        # 3. Token Warnings trigger prompt compression advice
        if statuses.get(ResourceCategory.TOKENS) in [BudgetStatus.WARNING, BudgetStatus.CRITICAL]:
            return (
                BudgetRecommendation.COMPRESS_PROMPT,
                "High token consumption: Trigger prompt memory compression.",
            )

        # 4. Screenshot Warnings trigger visual degradation advice
        if statuses.get(ResourceCategory.SCREENSHOTS) in [BudgetStatus.WARNING, BudgetStatus.CRITICAL]:
            return (
                BudgetRecommendation.DEGRADE_VISUALS,
                "Screenshot budget warning: Disable visual diffs or bounding box annotations.",
            )

        return (BudgetRecommendation.CONTINUE, "All resource budgets healthy.")
