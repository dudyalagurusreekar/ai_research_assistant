"""Scoring algorithms for memory retrieval and ranking."""

import math
import time
from typing import List

from tools.browser.memory.models import MemoryItem, RelevanceScore


class MemoryScorer:
    """Calculates relevance scores for memory retrieval."""

    def __init__(
        self,
        decay_rate: float = 0.99,  # How quickly recency weight decays
        similarity_weight: float = 0.6,
        recency_weight: float = 0.2,
        importance_weight: float = 0.2,
    ):
        self.decay_rate = decay_rate
        self.similarity_weight = similarity_weight
        self.recency_weight = recency_weight
        self.importance_weight = importance_weight

    def calculate_recency(self, timestamp: float, current_time: float) -> float:
        """Calculate exponential decay based on hours elapsed."""
        hours_elapsed = (current_time - timestamp) / 3600.0
        # Prevent negative elapsed time if clocks skew slightly
        hours_elapsed = max(0.0, hours_elapsed)
        return math.pow(self.decay_rate, hours_elapsed)

    def score(self, item: MemoryItem, semantic_similarity: float) -> RelevanceScore:
        """Calculate the total relevance score for a memory item."""
        current_time = time.time()
        recency = self.calculate_recency(item.timestamp, current_time)
        importance = item.importance

        final = (
            (semantic_similarity * self.similarity_weight) +
            (recency * self.recency_weight) +
            (importance * self.importance_weight)
        )

        return RelevanceScore(
            semantic_similarity=semantic_similarity,
            recency_weight=recency,
            importance_weight=importance,
            final_score=final,
        )

    def rank(self, items: List[tuple[MemoryItem, float]]) -> List[tuple[MemoryItem, RelevanceScore]]:
        """Rank a list of items and their raw similarity scores.
        
        Args:
            items: List of tuples (MemoryItem, semantic_similarity_float).
            
        Returns:
            Sorted list by final_score descending.
        """
        scored_items = []
        for item, sim in items:
            score = self.score(item, sim)
            scored_items.append((item, score))
            
        scored_items.sort(key=lambda x: x[1].final_score, reverse=True)
        return scored_items
