"""Comprehensive test suite for the Budget Manager.

Tests consumption limits, warnings, dynamic rebalancing, forecasting,
and escape recommendations.
"""

import pytest

from tools.browser.budget.base import (
    BudgetExceededError,
    BudgetLimit,
    BudgetRecommendation,
    BudgetStatus,
    ResourceCategory,
)
from tools.browser.budget.manager import BudgetManager


# ─────────────────────────────────────────────
# BudgetLimit Unit Tests
# ─────────────────────────────────────────────

class TestBudgetLimit:
    """Tests for the BudgetLimit boundaries DTO."""

    def test_limit_status_transitions(self):
        """Should resolve status based on consumption thresholds."""
        # 1. Healthy state (< 70%)
        limit = BudgetLimit(limit=100.0, consumed=50.0)
        assert limit.get_status() == BudgetStatus.HEALTHY
        assert limit.remaining == 50.0

        # 2. Warning state (>= 70%)
        limit.consumed = 75.0
        assert limit.get_status() == BudgetStatus.WARNING

        # 3. Critical state (>= 90%)
        limit.consumed = 92.0
        assert limit.get_status() == BudgetStatus.CRITICAL

        # 4. Exhausted state (>= 100%)
        limit.consumed = 100.0
        assert limit.get_status() == BudgetStatus.EXHAUSTED


# ─────────────────────────────────────────────
# BudgetManager Coordinator Tests
# ─────────────────────────────────────────────

class TestBudgetManager:
    """Tests for the central BudgetManager orchestrator."""

    def test_consume_succeeds(self):
        """Should accumulate resource usage under limit."""
        manager = BudgetManager()
        manager.consume(ResourceCategory.ACTIONS, 5)
        manager.consume(ResourceCategory.ACTIONS, 10)

        limit = manager.get_limit(ResourceCategory.ACTIONS)
        assert limit.consumed == 15.0
        assert limit.remaining == 10.0

    def test_consume_raises_exceeded(self):
        """Should raise BudgetExceededError and cap consumed at limit on overrun."""
        manager = BudgetManager()
        
        # Hard limit for actions is 25 by default
        with pytest.raises(BudgetExceededError) as exc_info:
            manager.consume(ResourceCategory.ACTIONS, 30)

        assert exc_info.value.category == "ACTIONS"
        assert exc_info.value.limit == 25.0
        
        limit = manager.get_limit(ResourceCategory.ACTIONS)
        assert limit.consumed == 25.0

    def test_reserve_and_release(self):
        """Should block capacity during reservation and free it upon release."""
        manager = BudgetManager()
        
        # Reserve 10 ACTIONS
        manager.reserve(ResourceCategory.ACTIONS, 10)
        limit = manager.get_limit(ResourceCategory.ACTIONS)
        
        assert limit.reserved == 10.0
        assert limit.remaining == 15.0  # Limit (25) - consumed (0) - reserved (10)

        # Release 5 actions
        manager.release(ResourceCategory.ACTIONS, 5)
        assert limit.reserved == 5.0
        assert limit.remaining == 20.0

    def test_rebalance(self):
        """Should transfer limit capacity between source and target categories."""
        manager = BudgetManager()
        
        # ACTIONS: limit=25, TOKENS: limit=150000
        manager.rebalance(ResourceCategory.ACTIONS, ResourceCategory.TOKENS, 5.0)

        actions_limit = manager.get_limit(ResourceCategory.ACTIONS)
        tokens_limit = manager.get_limit(ResourceCategory.TOKENS)

        assert actions_limit.limit == 20.0
        assert tokens_limit.limit == 150005.0

    def test_forecast_remaining_capacity(self):
        """Should accurately estimate remaining steps before exhaustion."""
        manager = BudgetManager()
        
        # Consumed 15/25 ACTIONS. 10 units left.
        manager.consume(ResourceCategory.ACTIONS, 15)
        
        # Consuming at rate of 2 actions per reasoning step
        steps_left = manager.forecast_capacity(ResourceCategory.ACTIONS, 2.0)
        assert steps_left == 5.0

        # Rate of 0 returns safe default
        assert manager.forecast_capacity(ResourceCategory.ACTIONS, 0.0) == 999.0


# ─────────────────────────────────────────────
# Dynamic Recommendation & Workflow Scenarios
# ─────────────────────────────────────────────

class TestBudgetAdvisoryScenarios:
    """Tests checking trigger boundaries for adaptive degradation advices."""

    def test_continue_on_healthy(self):
        """Should recommend CONTINUE when all resource limits are healthy."""
        manager = BudgetManager()
        rec, msg = manager.get_recommendation()
        assert rec == BudgetRecommendation.CONTINUE
        assert "healthy" in msg.lower()

    def test_prompt_compression_trigger(self):
        """Should recommend COMPRESS_PROMPT when token usage exceeds 70%."""
        manager = BudgetManager()
        # default token limit is 150k
        manager.consume(ResourceCategory.TOKENS, 110000)  # > 73%
        
        rec, msg = manager.get_recommendation()
        assert rec == BudgetRecommendation.COMPRESS_PROMPT
        assert "token" in msg.lower()

    def test_degrade_visuals_trigger(self):
        """Should recommend DEGRADE_VISUALS when screenshot count exceeds 70%."""
        manager = BudgetManager()
        # default screenshot limit is 30
        manager.consume(ResourceCategory.SCREENSHOTS, 22)  # > 73%

        rec, msg = manager.get_recommendation()
        assert rec == BudgetRecommendation.DEGRADE_VISUALS
        assert "screenshot" in msg.lower()

    def test_replan_exploration_trigger(self):
        """Should recommend REPLAN_EXPLORATION when steps count exceeds 90%."""
        manager = BudgetManager()
        # default step limit is 15
        manager.consume(ResourceCategory.STEPS, 14)  # 14/15 = 93%

        rec, msg = manager.get_recommendation()
        assert rec == BudgetRecommendation.REPLAN_EXPLORATION
        assert "step" in msg.lower()

    def test_emergency_shutdown_trigger(self):
        """Should recommend SHUTDOWN upon exhaustion of any hard limits."""
        manager = BudgetManager()
        
        # Force ACTIONS limit to be exceeded (caps at limit and triggers exhaustion status)
        try:
            manager.consume(ResourceCategory.ACTIONS, 30)
        except BudgetExceededError:
            pass

        rec, msg = manager.get_recommendation()
        assert rec == BudgetRecommendation.SHUTDOWN
        assert "exhausted" in msg.lower()
