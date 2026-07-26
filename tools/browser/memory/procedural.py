"""Procedural Memory layer for reusable workflows and successful selectors."""

import logging
from typing import List, Dict, Any, Optional

from tools.browser.memory.models import MemoryItem, MemoryType, RelevanceScore
from tools.browser.memory.vector_store import BaseVectorStore
from tools.browser.memory.scorer import MemoryScorer

logger = logging.getLogger("ProceduralMemory")


class ProceduralMemory:
    """The 'How-To' repository.
    
    Stores abstract, reusable execution strategies, robust task graphs, 
    and fallback selectors discovered by the Recovery Engine.
    """

    def __init__(self, store: BaseVectorStore, scorer: MemoryScorer):
        self.store = store
        self.scorer = scorer

    def store_alternative_selector(self, domain: str, original_selector: str, working_selector: str) -> None:
        """Store a successful selector discovered during recovery."""
        content = f"Domain: {domain} | Failed Selector: {original_selector} | Working Selector: {working_selector}"
        item = MemoryItem(
            content=content,
            memory_type=MemoryType.PROCEDURAL,
            importance=0.9, # Very important for future robustness
            metadata={
                "domain": domain,
                "type": "selector_mapping",
                "original": original_selector,
                "working": working_selector
            }
        )
        self.store.add(item)
        logger.debug(f"Stored procedural selector mapping for {domain}")

    def store_strategy(self, task_type: str, strategy_description: str, success_rate: float = 1.0) -> None:
        """Store a high-level approach to solving a specific type of task."""
        content = f"Task Type: {task_type} | Strategy: {strategy_description}"
        item = MemoryItem(
            content=content,
            memory_type=MemoryType.PROCEDURAL,
            importance=0.8,
            metadata={
                "type": "strategy",
                "task_type": task_type,
                "success_rate": success_rate
            }
        )
        self.store.add(item)

    def retrieve_strategy(self, task_description: str, limit: int = 3) -> List[tuple[MemoryItem, RelevanceScore]]:
        """Find a reusable strategy or plan for a given task."""
        raw_results = self.store.search(task_description, limit=limit * 3)
        
        procedural_results = []
        for item, sim in raw_results:
            if item.memory_type == MemoryType.PROCEDURAL and item.metadata.get("type") == "strategy":
                procedural_results.append((item, sim))
                
        ranked = self.scorer.rank(procedural_results)
        
        for item, score in ranked[:limit]:
            item.touch()
            self.store.add(item)
            
        return ranked[:limit]

    def get_known_selectors(self, domain: str, failed_selector: str) -> List[str]:
        """Check if we know a working alternative for a failed selector on this domain."""
        query = f"Domain: {domain} | Failed Selector: {failed_selector}"
        raw_results = self.store.search(query, limit=5)
        
        alternatives = []
        for item, sim in raw_results:
            if (item.memory_type == MemoryType.PROCEDURAL and 
                item.metadata.get("type") == "selector_mapping" and
                item.metadata.get("domain") == domain):
                
                # If similarity is high, or it specifically matches our failed selector
                if sim > 0.7 or item.metadata.get("original") == failed_selector:
                    alt = item.metadata.get("working")
                    if alt and alt not in alternatives:
                        alternatives.append(alt)
                        item.touch()
                        self.store.add(item)
                        
        return alternatives
