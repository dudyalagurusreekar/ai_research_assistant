"""Core compression strategies for context optimization.

Implements semantic deduplication, extractive relevance filters, abstractive summaries,
and recency weighting patterns.
"""

from typing import Any, Dict, List, Tuple

from tools.browser.compressor.base import BaseCompressorStrategy, CompressionStrategyType


class SemanticDeduplicationStrategy(BaseCompressorStrategy):
    """Consolidates consecutive identical actions into a single summary step."""

    @property
    def strategy_type(self) -> CompressionStrategyType:
        return CompressionStrategyType.DEDUPLICATION

    def compress(
        self,
        steps: List[Dict[str, Any]],
        max_tokens_target: int,
        is_aggressive: bool = False,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        if not steps:
            return [], []

        deduplicated: List[Dict[str, Any]] = []
        preserved_checkpoints = []

        current_block: List[Dict[str, Any]] = []

        for step in steps:
            # Check for checkpoints to preserve
            if step.get("recovery_strategy") or step.get("is_checkpoint"):
                preserved_checkpoints.append(
                    f"Checkpoint step {step.get('step_number')}: {step.get('command') or step.get('action')}"
                )

            if not current_block:
                current_block.append(step)
                continue

            # Compare step signatures
            last_step = current_block[-1]
            last_sig = (last_step.get("action") or last_step.get("command"), last_step.get("selector"))
            current_sig = (step.get("action") or step.get("command"), step.get("selector"))

            # Dedup conditions: same action + selector, or repeated scrollings
            is_dup = (last_sig == current_sig and last_sig[0] is not None)
            is_scroll = (last_sig[0] == "scroll" and current_sig[0] == "scroll")

            if is_dup or is_scroll:
                current_block.append(step)
            else:
                # Flush block
                deduplicated.append(self._consolidate_block(current_block))
                current_block = [step]

        if current_block:
            deduplicated.append(self._consolidate_block(current_block))

        return deduplicated, preserved_checkpoints

    def _consolidate_block(self, block: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge a sequence of repeated steps into a consolidated representation."""
        if len(block) == 1:
            return block[0]

        head = block[0]
        action = head.get("action") or head.get("command") or ""
        selector = head.get("selector") or ""
        
        consolidated = dict(head)
        consolidated["result_message"] = (
            f"Consolidated Block: Repeated '{action}' action on '{selector}' "
            f"{len(block)} times consecutive. Final outcome: {block[-1].get('success', False)}"
        )
        # Keep success of the final step in sequence
        consolidated["success"] = block[-1].get("success", False)
        consolidated["consolidated_count"] = len(block)
        return consolidated


class ExtractiveCompressorStrategy(BaseCompressorStrategy):
    """Filters low-importance steps while preserving critical checkpoints, inputs, and artifacts."""

    @property
    def strategy_type(self) -> CompressionStrategyType:
        return CompressionStrategyType.EXTRACTIVE

    def compress(
        self,
        steps: List[Dict[str, Any]],
        max_tokens_target: int,
        is_aggressive: bool = False,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        if not steps:
            return [], []

        preserved_checkpoints = []
        filtered_steps = []

        for step in steps:
            # Importance scoring rules
            score = 1  # Base score
            
            action = (step.get("action") or step.get("command") or "").lower()
            success = step.get("success", False)
            
            # High-priority factors
            if step.get("recovery_strategy") or step.get("is_checkpoint"):
                score += 10
                preserved_checkpoints.append(f"Recovery Checkpoint: {action}")
            if any(w in action for w in ["download", "upload", "submit", "login"]):
                score += 5
            if not success:
                # Keep failures for planner logic re-routing
                score += 4
            if step.get("text_input") or step.get("text"):
                # Forms fill data is important
                score += 3

            # Low-priority factors
            if action in ["hover", "scroll", "wait_for_network_idle"]:
                score -= 1

            # Decide step inclusion
            threshold = 3 if is_aggressive else 2
            if score >= threshold:
                filtered_steps.append(step)
            else:
                # Summarize filtered steps to preserve minimal trace
                step_num = step.get("step_number", "?")
                filtered_steps.append({
                    "step_number": step_num,
                    "command": f"omitted_{action}",
                    "result_message": f"Omitted low-priority action step {step_num}",
                    "success": success,
                })

        return filtered_steps, preserved_checkpoints


class AbstractiveCompressorStrategy(BaseCompressorStrategy):
    """Replaces older steps with a compact template-driven summary lines."""

    @property
    def strategy_type(self) -> CompressionStrategyType:
        return CompressionStrategyType.ABSTRACTIVE

    def compress(
        self,
        steps: List[Dict[str, Any]],
        max_tokens_target: int,
        is_aggressive: bool = False,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        if not steps:
            return [], []

        preserved_checkpoints = []
        success_count = sum(1 for s in steps if s.get("success", False))
        actions_list = [s.get("action") or s.get("command") or "unknown" for s in steps]
        actions_counts = {}
        for act in actions_list:
            actions_counts[act] = actions_counts.get(act, 0) + 1

        actions_summary = ", ".join(f"{count} {act}" for act, count in actions_counts.items())
        step_range = f"Steps {steps[0].get('step_number', 1)} to {steps[-1].get('step_number', len(steps))}"

        summary_step = {
            "step_number": steps[0].get("step_number", 1),
            "command": "history_summary",
            "result_message": (
                f"{step_range} consolidated summary: Executed {len(steps)} total actions "
                f"({actions_summary}). Successes: {success_count}/{len(steps)}."
            ),
            "success": all(s.get("success", False) for s in steps),
        }

        # Keep checkpoints preserved in metadata
        for s in steps:
            if s.get("recovery_strategy") or s.get("is_checkpoint"):
                preserved_checkpoints.append(
                    f"Consolidated Checkpoint {s.get('step_number')}: {s.get('command') or s.get('action')}"
                )

        return [summary_step], preserved_checkpoints


class RecencyWeightingStrategy(BaseCompressorStrategy):
    """Retains detailed recent history steps while compressing older historical traces."""

    def __init__(self, recent_count: int = 3) -> None:
        self.recent_count = recent_count

    @property
    def strategy_type(self) -> CompressionStrategyType:
        return CompressionStrategyType.RECENCY

    def compress(
        self,
        steps: List[Dict[str, Any]],
        max_tokens_target: int,
        is_aggressive: bool = False,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        if len(steps) <= self.recent_count:
            return steps, []

        preserved_checkpoints = []
        
        # Divide into older and recent steps
        older_steps = steps[:-self.recent_count]
        recent_steps = steps[-self.recent_count:]

        # Compress older steps using Abstractive summarization
        abstractive = AbstractiveCompressorStrategy()
        compressed_older, older_checkpoints = abstractive.compress(
            older_steps, max_tokens_target, is_aggressive
        )
        preserved_checkpoints.extend(older_checkpoints)

        # Merge results
        result_steps = compressed_older + recent_steps
        return result_steps, preserved_checkpoints
