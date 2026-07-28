"""Memory Consolidator implementing importance decay, summarization, and forgetting policies."""

from typing import List
from tools.memory.interfaces.memory_interfaces import IMemoryConsolidator, IMemoryProvider
from tools.memory.models.memory_models import MemoryType, MemoryConsolidationResult
from infrastructure.logging.logger import StructuredLogger


class MemoryConsolidator(IMemoryConsolidator):
    """Engine responsible for memory consolidation, importance decay, summarization, and pruning."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("MemoryConsolidator")

    async def consolidate(self, providers: List[IMemoryProvider]) -> MemoryConsolidationResult:
        """Run consolidation cycle across registered memory providers."""
        result = MemoryConsolidationResult()

        provider_map = {p.memory_type: p for p in providers}
        short_term_p = provider_map.get(MemoryType.SHORT_TERM)
        long_term_p = provider_map.get(MemoryType.LONG_TERM)

        # 1. Decay and Consolidate Short-Term Memories
        if short_term_p:
            items = await short_term_p.list_all()
            for item in items:
                # Apply slight importance decay
                item.importance = round(max(0.05, item.importance * 0.95), 4)
                result.decayed_count += 1

                # Transfer high-value or frequently accessed items to Long-Term Storage
                if long_term_p and (item.importance >= 0.75 or item.access_count >= 2):
                    item.memory_type = MemoryType.LONG_TERM
                    await long_term_p.store(item)
                    result.consolidated_count += 1

                # Prune insignificant low-importance items
                elif item.importance <= 0.10 and item.access_count == 0:
                    await short_term_p.delete(item.memory_id)
                    result.pruned_count += 1

        self._logger.info(
            f"Consolidation cycle completed: {result.consolidated_count} consolidated, "
            f"{result.decayed_count} decayed, {result.pruned_count} pruned."
        )
        return result
