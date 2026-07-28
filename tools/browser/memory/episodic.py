"""Episodic Memory layer for execution history and logs."""

import logging
from typing import List

from tools.browser.memory.models import MemoryItem, MemoryType, RelevanceScore
from tools.browser.memory.vector_store import BaseVectorStore
from tools.browser.memory.scorer import MemoryScorer

logger = logging.getLogger("EpisodicMemory")


class EpisodicMemory:
    """Chronological ledger of executions (Action -> State -> Result).
    
    Stores full task traces, distinguishing between successful workflows
    and failed attempts. Backed by a vector store for semantic retrieval.
    """

    def __init__(self, store: BaseVectorStore, scorer: MemoryScorer):
        self.store = store
        self.scorer = scorer

    def log_execution(self, action: str, selector: str, success: bool, error: str = "") -> None:
        """Log a single atomic action execution."""
        content = f"Action: {action} | Selector: {selector} | Success: {success}"
        if error:
            content += f" | Error: {error}"
            
        item = MemoryItem(
            content=content,
            memory_type=MemoryType.EPISODIC,
            importance=0.8 if not success else 0.4, # Failures are often more important to remember
            metadata={"action": action, "selector": selector, "success": success}
        )
        self.store.add(item)
        logger.debug(f"Logged episodic memory: {item.id}")

    def log_workflow(self, goal: str, steps_summary: str, success: bool) -> None:
        """Log a completed high-level workflow/task."""
        content = f"Workflow Goal: {goal}\nOutcome: {'SUCCESS' if success else 'FAILURE'}\nSummary: {steps_summary}"
        
        item = MemoryItem(
            content=content,
            memory_type=MemoryType.EPISODIC,
            importance=0.9,
            metadata={"goal": goal, "success": success, "type": "workflow_summary"}
        )
        self.store.add(item)

    def retrieve_similar_experiences(self, query: str, limit: int = 5) -> List[tuple[MemoryItem, RelevanceScore]]:
        """Find past experiences similar to the query."""
        raw_results = self.store.search(query, limit=limit * 2)
        
        # Filter to only episodic memories if store is shared
        episodic_results = [(item, sim) for item, sim in raw_results if item.memory_type == MemoryType.EPISODIC]
        
        ranked = self.scorer.rank(episodic_results)
        
        # Update access count for top results
        for item, score in ranked[:limit]:
            item.touch()
            self.store.add(item) # re-save to persist updated access count
            
        return ranked[:limit]
