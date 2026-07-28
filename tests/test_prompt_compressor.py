"""Comprehensive test suite for the Prompt Compressor.

Tests context summarization strategies, deduplication, recency weighting,
and budget-aware scaling limits.
"""

from unittest.mock import MagicMock

from tools.browser.budget import BudgetLimit, BudgetManager, BudgetStatus
from tools.browser.compressor.pipeline import PromptCompressor
from tools.browser.compressor.strategies import (
    AbstractiveCompressorStrategy,
    ExtractiveCompressorStrategy,
    RecencyWeightingStrategy,
    SemanticDeduplicationStrategy,
)


# ─────────────────────────────────────────────
# Individual Strategies Unit Tests
# ─────────────────────────────────────────────

class TestCompressionStrategies:
    """Tests verifying behavior of individual prompt compressor strategies."""

    def test_semantic_deduplication(self):
        """Should consolidate consecutive repeating actions into single entries."""
        steps = [
            {"step_number": 1, "action": "click", "selector": "#btn", "success": True},
            {"step_number": 2, "action": "click", "selector": "#btn", "success": True},
            {"step_number": 3, "action": "click", "selector": "#btn", "success": True},
            {"step_number": 4, "action": "type_text", "selector": "#field", "success": True},
        ]
        strategy = SemanticDeduplicationStrategy()
        compressed, checkpoints = strategy.compress(steps, 4000)

        assert len(compressed) == 2
        assert compressed[0]["consolidated_count"] == 3
        assert "consolidated block" in compressed[0]["result_message"].lower()
        assert compressed[1]["action"] == "type_text"

    def test_extractive_filter_normal(self):
        """Should filter out low-importance actions like scroll or hover."""
        steps = [
            {"step_number": 1, "action": "click", "selector": "#submit", "success": True},
            {"step_number": 2, "action": "scroll", "selector": "window", "success": True},
            {"step_number": 3, "action": "download_file", "selector": "#link", "success": True},
        ]
        strategy = ExtractiveCompressorStrategy()
        compressed, checkpoints = strategy.compress(steps, 4000, is_aggressive=False)

        # In normal mode, scroll has low score (0) and is omitted. Others remain.
        assert len(compressed) == 3
        assert compressed[1]["command"] == "omitted_scroll"
        assert "omitted" in compressed[1]["result_message"].lower()

    def test_extractive_filter_aggressive(self):
        """Should selectively filter steps under aggressive settings."""
        steps = [
            {"step_number": 1, "action": "click", "selector": "#submit", "success": True},  # score = 1 (low)
            {"step_number": 2, "action": "download_file", "selector": "#link", "success": True},  # score = 6 (high)
        ]
        strategy = ExtractiveCompressorStrategy()
        compressed, checkpoints = strategy.compress(steps, 4000, is_aggressive=True)

        assert len(compressed) == 2
        assert compressed[0]["command"] == "omitted_click"
        assert compressed[1]["action"] == "download_file"

    def test_abstractive_summarization(self):
        """Should replace the steps list with a single template summary step."""
        steps = [
            {"step_number": 1, "action": "click", "success": True},
            {"step_number": 2, "action": "click", "success": True},
            {"step_number": 3, "action": "fill_input", "success": True},
        ]
        strategy = AbstractiveCompressorStrategy()
        compressed, checkpoints = strategy.compress(steps, 4000)

        assert len(compressed) == 1
        summary = compressed[0]
        assert summary["command"] == "history_summary"
        assert "steps 1 to 3 consolidated summary" in summary["result_message"].lower()
        assert "2 click, 1 fill_input" in summary["result_message"]

    def test_recency_weighting(self):
        """Should retain only recent detailed steps and summarize the older ones."""
        steps = [
            {"step_number": 1, "action": "click", "success": True},
            {"step_number": 2, "action": "click", "success": True},
            {"step_number": 3, "action": "type_text", "success": True},
            {"step_number": 4, "action": "download_file", "success": True},
        ]
        strategy = RecencyWeightingStrategy(recent_count=2)
        compressed, checkpoints = strategy.compress(steps, 4000)

        # Should summarize steps 1 & 2 into 1 step, and keep 3 & 4 detailed.
        assert len(compressed) == 3
        assert compressed[0]["command"] == "history_summary"
        assert compressed[1]["action"] == "type_text"
        assert compressed[2]["action"] == "download_file"


# ─────────────────────────────────────────────
# Pipeline Coordinator Integration Tests
# ─────────────────────────────────────────────

class TestPromptCompressorPipeline:
    """Integration and coordination tests for the PromptCompressor pipeline."""

    def test_token_estimation(self):
        """Should estimate tokens based on character length ratio."""
        compressor = PromptCompressor(char_to_token_ratio=4.0)
        assert compressor.estimate_tokens("12345678") == 2
        assert compressor.estimate_tokens("") == 0

    def test_compress_preserves_checkpoints_and_constraints(self):
        """Preserved constraints and custom checkpoints should remain intact."""
        steps = [
            {"step_number": 1, "action": "click", "selector": "#btn-1", "success": True, "is_checkpoint": True},
            {"step_number": 2, "action": "click", "selector": "#btn-2", "success": True},
        ]
        
        compressor = PromptCompressor()
        res = compressor.compress_prompt(
            steps=steps,
            user_constraints="Always write output to results.json",
            system_instructions="You are an autonomous browser agent."
        )

        assert res.original_tokens > 0
        assert res.compressed_tokens > 0
        assert res.compression_ratio > 0.0
        
        # Verify text elements exist in output
        assert "You are an autonomous browser agent." in res.compressed_text
        assert "Always write output to results.json" in res.compressed_text
        assert "results.json" in res.compressed_text
        assert len(res.preserved_checkpoints) == 2
        assert any("step 1" in c for c in res.preserved_checkpoints)

    def test_budget_aware_aggressive_compression(self):
        """Should automatically trigger aggressive mode if BudgetManager warns of tokens usage limit."""
        # 1. Healthy budget
        mock_budget = MagicMock(spec=BudgetManager)
        mock_limit = MagicMock(spec=BudgetLimit)
        mock_limit.get_status.return_value = BudgetStatus.HEALTHY
        mock_budget.get_limit.return_value = mock_limit

        steps = [
            {"step_number": 1, "action": "click", "selector": "#btn-1", "success": True},
            {"step_number": 2, "action": "click", "selector": "#btn-1", "success": True},
            {"step_number": 3, "action": "click", "selector": "#btn-1", "success": True},
            {"step_number": 4, "action": "hover", "selector": "#element", "success": True},
        ]

        compressor = PromptCompressor(budget_manager=mock_budget)
        res_healthy = compressor.compress_prompt(steps=steps)
        assert res_healthy.details["is_aggressive"] is False

        # 2. Warning budget
        mock_limit.get_status.return_value = BudgetStatus.WARNING
        res_warning = compressor.compress_prompt(steps=steps)
        
        assert res_warning.details["is_aggressive"] is True
        # In aggressive mode, hover should be filtered out (omitted)
        assert "omitted" in res_warning.compressed_text.lower()
