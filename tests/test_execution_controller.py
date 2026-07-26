"""Unit tests for the ExecutionController."""

import unittest
from tools.browser.planner.controller import (
    ExecutionController,
    BudgetExceededError,
    LoopDetectedError,
)


class TestExecutionController(unittest.TestCase):
    """Test suite for ExecutionController functionality."""

    def test_action_budget_exceeded(self):
        """Verify that performing more actions than max_actions raises BudgetExceededError."""
        controller = ExecutionController(max_actions=2)
        controller.record_action()  # Action 1
        controller.record_action()  # Action 2
        with self.assertRaises(BudgetExceededError):
            controller.record_action()  # Action 3 (exceeds budget)

    def test_token_budget_exceeded(self):
        """Verify that token consumption above limit raises BudgetExceededError."""
        controller = ExecutionController(max_tokens=100)
        
        # Add usage below limit
        controller.record_token_usage({"total_tokens": 50})
        self.assertEqual(controller.total_tokens_used, 50)
        
        # Exceed limit
        with self.assertRaises(BudgetExceededError):
            controller.record_token_usage({"total_tokens": 60})

    def test_loop_detection(self):
        """Verify that repeating identical failed actions triggers LoopDetectedError."""
        controller = ExecutionController(max_consecutive_failures=3)
        signature = "click_#submit_None"
        
        controller.check_loop(signature, success=False)  # 1
        controller.check_loop(signature, success=False)  # 2
        with self.assertRaises(LoopDetectedError):
            controller.check_loop(signature, success=False)  # 3 (triggers loop error)

    def test_loop_counter_resets_on_success(self):
        """Verify that a successful action resets the consecutive failure counter."""
        controller = ExecutionController(max_consecutive_failures=3)
        signature = "click_#submit_None"
        
        controller.check_loop(signature, success=False)  # 1
        controller.check_loop(signature, success=False)  # 2
        controller.check_loop(signature, success=True)   # Reset!
        self.assertEqual(controller.consecutive_failures, 0)
        
        # Should not raise error on next 2 failures
        controller.check_loop(signature, success=False)  # 1
        controller.check_loop(signature, success=False)  # 2


if __name__ == "__main__":
    unittest.main()
