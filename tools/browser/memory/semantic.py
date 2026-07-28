"""Semantic Memory layer for factual knowledge and site schemas."""

import logging
from typing import List, Dict, Any

from tools.browser.memory.models import MemoryItem, MemoryType, RelevanceScore
from tools.browser.memory.vector_store import BaseVectorStore
from tools.browser.memory.scorer import MemoryScorer

logger = logging.getLogger("SemanticMemory")


class SemanticMemory:
    """Factual knowledge base.
    
    Stores website-specific layouts (e.g., "GitHub login requires 2FA"),
    user preferences, and extracted structured data.
    """

    def __init__(self, store: BaseVectorStore, scorer: MemoryScorer):
        self.store = store
        self.scorer = scorer

    def store_fact(self, domain: str, fact: str, importance: float = 0.7) -> None:
        """Store a factual piece of knowledge about a domain."""
        content = f"Domain: {domain} | Fact: {fact}"
        item = MemoryItem(
            content=content,
            memory_type=MemoryType.SEMANTIC,
            importance=importance,
            metadata={"domain": domain, "fact_type": "general"}
        )
        self.store.add(item)
        logger.debug(f"Stored semantic fact for {domain}: {fact}")

    def store_schema(self, domain: str, schema_name: str, schema_data: Dict[str, Any]) -> None:
        """Store structured schema understanding (e.g., login form structure)."""
        # Convert dict to string representation for semantic search
        schema_str = ", ".join(f"{k}: {v}" for k, v in schema_data.items())
        content = f"Domain: {domain} | Schema: {schema_name} | Layout: {schema_str}"
        
        item = MemoryItem(
            content=content,
            memory_type=MemoryType.SEMANTIC,
            importance=0.9,
            metadata={"domain": domain, "schema_name": schema_name, "data": schema_data}
        )
        self.store.add(item)

    def retrieve_domain_knowledge(self, domain: str, query: str = "", limit: int = 5) -> List[tuple[MemoryItem, RelevanceScore]]:
        """Retrieve semantic knowledge for a specific domain."""
        search_query = f"Domain: {domain} {query}".strip()
        raw_results = self.store.search(search_query, limit=limit * 3)
        
        # Filter for semantic memory and matching domain
        semantic_results = []
        for item, sim in raw_results:
            if item.memory_type == MemoryType.SEMANTIC:
                if item.metadata.get("domain") == domain or domain in item.content:
                    semantic_results.append((item, sim))
                    
        ranked = self.scorer.rank(semantic_results)
        
        for item, score in ranked[:limit]:
            item.touch()
            self.store.add(item)
            
        return ranked[:limit]
