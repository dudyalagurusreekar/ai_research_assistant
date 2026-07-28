"""Prompt Compressor Coordinator Pipeline.

Manages strategy chains, estimates token usage, checks BudgetManager status,
and compiles the optimized CompressedContext.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from tools.browser.budget.base import BudgetStatus, ResourceCategory
from tools.browser.budget.manager import BudgetManager
from tools.browser.compressor.base import (
    BaseCompressorStrategy,
    CompressedContext,
)
from tools.browser.compressor.strategies import (
    ExtractiveCompressorStrategy,
    RecencyWeightingStrategy,
    SemanticDeduplicationStrategy,
)

logger = logging.getLogger("PromptCompressor.Pipeline")


class PromptCompressor:
    """Enterprise Prompt Compressor coordinating context summarization and token reduction.

    Attributes:
        budget_manager: Reference to the active BudgetManager.
        strategies: Active compression strategies chain.
        char_to_token_ratio: Estimation ratio factor (default 4.0 chars per token).
    """

    def __init__(
        self,
        budget_manager: Optional[BudgetManager] = None,
        strategies: Optional[List[BaseCompressorStrategy]] = None,
        char_to_token_ratio: float = 4.0,
    ) -> None:
        """Initialize the Prompt Compressor.

        Args:
            budget_manager: Active budget limits tracker.
            strategies: Custom strategies execution chain.
            char_to_token_ratio: Substring character count token ratio estimator.
        """
        self.budget_manager = budget_manager
        self.strategies = strategies or [
            SemanticDeduplicationStrategy(),
            RecencyWeightingStrategy(recent_count=2),
            ExtractiveCompressorStrategy(),
        ]
        self.char_to_token_ratio = char_to_token_ratio
        self._logger = logger

    def estimate_tokens(self, text: str) -> int:
        """Estimate the token length of a text string.

        Args:
            text: Text to evaluate.

        Returns:
            int: Estimated token count.
        """
        if not text:
            return 0
        return int(len(text) / self.char_to_token_ratio)

    def compress_prompt(
        self,
        steps: List[Dict[str, Any]],
        user_constraints: Optional[str] = None,
        system_instructions: Optional[str] = None,
        max_tokens_target: int = 4000,
    ) -> CompressedContext:
        """Compress execution history steps list and build the optimized prompt text.

        Args:
            steps: Complete reasoning steps trace list.
            user_constraints: Constraints to keep preserved at the top of context.
            system_instructions: Instructions preserved.
            max_tokens_target: Maximum target token window.

        Returns:
            CompressedContext: DTO with optimized content.
        """
        # 1. Determine compression level aggressiveness from BudgetManager
        is_aggressive = False
        if self.budget_manager:
            status = self.budget_manager.get_limit(ResourceCategory.TOKENS).get_status()
            if status in [BudgetStatus.WARNING, BudgetStatus.CRITICAL]:
                is_aggressive = True
                self._logger.warning(
                    f"Prompt Compressor triggered AGGRESSIVE mode due to "
                    f"BudgetManager TOKENS status={status.value}."
                )

        # 2. Serialize initial input to calculate raw metrics
        raw_steps_str = json.dumps(steps, indent=2)
        total_raw_text = (
            (system_instructions or "")
            + (user_constraints or "")
            + raw_steps_str
        )
        original_tokens = self.estimate_tokens(total_raw_text)

        # 3. Iterate through strategies chain to compress steps
        compressed_steps = list(steps)
        preserved_checkpoints: List[str] = []

        for strategy in self.strategies:
            try:
                compressed_steps, checkpoints = strategy.compress(
                    compressed_steps, max_tokens_target, is_aggressive
                )
                preserved_checkpoints.extend(checkpoints)
            except Exception as e:
                self._logger.error(f"Strategy '{strategy.strategy_type.value}' failed: {e}")

        # 4. Serialize output steps
        compressed_steps_str = json.dumps(compressed_steps, indent=2)
        
        # 5. Build final compressed context text
        final_prompt_parts = []
        if system_instructions:
            final_prompt_parts.append(f"System Instructions:\n{system_instructions}\n")
        if user_constraints:
            final_prompt_parts.append(f"User Constraints (Preserved):\n{user_constraints}\n")
        if preserved_checkpoints:
            checkpoints_text = "\n".join(f"- {c}" for c in set(preserved_checkpoints))
            final_prompt_parts.append(f"Preserved Checkpoints:\n{checkpoints_text}\n")
        
        final_prompt_parts.append(f"Compressed History Steps:\n{compressed_steps_str}")
        compressed_text = "\n".join(final_prompt_parts)

        # 6. Resolve post-compression metrics
        compressed_tokens = self.estimate_tokens(compressed_text)
        compression_ratio = (compressed_tokens / original_tokens) if original_tokens > 0 else 1.0

        self._logger.info(
            f"Prompt compression completed: original_tokens={original_tokens}, "
            f"compressed_tokens={compressed_tokens}, "
            f"ratio={compression_ratio:.1%}"
        )

        return CompressedContext(
            compressed_text=compressed_text,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compression_ratio,
            preserved_checkpoints=list(set(preserved_checkpoints)),
            details={
                "steps_count_before": len(steps),
                "steps_count_after": len(compressed_steps),
                "is_aggressive": is_aggressive,
            },
        )
