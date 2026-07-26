"""Memory Manager Orchestrator.

Provides the high-level facade for integrating memory capabilities
into the browser agent subsystems.
"""

import logging
from typing import Optional

from tools.browser.memory.vector_store import BaseVectorStore, LightweightTFIDFStore
from tools.browser.memory.scorer import MemoryScorer
from tools.browser.memory.working import WorkingMemory
from tools.browser.memory.episodic import EpisodicMemory
from tools.browser.memory.semantic import SemanticMemory
from tools.browser.memory.procedural import ProceduralMemory

logger = logging.getLogger("MemoryManager")


class MemoryManager:
    """Top-level facade that coordinates all memory layers."""

    def __init__(
        self,
        persist_path: Optional[str] = None,
        store: Optional[BaseVectorStore] = None,
        scorer: Optional[MemoryScorer] = None,
    ):
        self.store = store or LightweightTFIDFStore(persist_path=persist_path)
        self.scorer = scorer or MemoryScorer()
        
        # Initialize layers
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory(self.store, self.scorer)
        self.semantic = SemanticMemory(self.store, self.scorer)
        self.procedural = ProceduralMemory(self.store, self.scorer)
        
        logger.info(f"MemoryManager initialized with store: {type(self.store).__name__}")

    def consolidate(self) -> None:
        """Move data from volatile working memory into long-term vector storage."""
        if not self.working.active_goal or not self.working.recent_steps:
            return
            
        summary_item = self.working.summarize()
        self.store.add(summary_item)
        
        # Extract potential procedural/semantic facts from summary
        goal = self.working.active_goal
        success = sum(1 for s in self.working.recent_steps if s["success"]) > 0
        
        # Log to episodic history
        self.episodic.log_workflow(
            goal=goal,
            steps_summary=summary_item.content,
            success=success
        )
        
        # Clear working memory for next task
        self.working.clear()
        logger.debug("Memory consolidation complete.")

    def get_relevant_context(self, task_description: str, domain: str = "") -> str:
        """Fetch a unified context string for the planner based on current task."""
        context_parts = []
        
        if domain:
            semantic = self.semantic.retrieve_domain_knowledge(domain, limit=2)
            if semantic:
                context_parts.append("Known Site Facts:")
                for item, score in semantic:
                    context_parts.append(f"- {item.content}")
                    
        procedural = self.procedural.retrieve_strategy(task_description, limit=2)
        if procedural:
            context_parts.append("\nProven Strategies:")
            for item, score in procedural:
                context_parts.append(f"- {item.content}")
                
        episodic = self.episodic.retrieve_similar_experiences(task_description, limit=2)
        if episodic:
            context_parts.append("\nSimilar Past Executions:")
            for item, score in episodic:
                context_parts.append(f"- {item.content}")
                
        return "\n".join(context_parts)
