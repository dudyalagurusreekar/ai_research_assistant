"""Vector storage and retrieval interfaces for memory."""

import abc
import collections
import json
import logging
import math
import os
from typing import List, Dict, Any, Optional

from tools.browser.memory.models import MemoryItem

logger = logging.getLogger("VectorStore")


class BaseVectorStore(abc.ABC):
    """Abstract base class for semantic memory storage."""

    @abc.abstractmethod
    def add(self, item: MemoryItem) -> None:
        """Add a memory item to the store."""

    @abc.abstractmethod
    def search(self, query: str, limit: int = 5) -> List[tuple[MemoryItem, float]]:
        """Search for memories matching the query.
        
        Returns:
            List of tuples (MemoryItem, raw_similarity_score).
        """

    @abc.abstractmethod
    def remove(self, item_id: str) -> bool:
        """Remove an item by ID."""
        
    @abc.abstractmethod
    def clear(self) -> None:
        """Clear all memories."""


class LightweightTFIDFStore(BaseVectorStore):
    """A zero-dependency, local fallback store using basic TF-IDF for semantic search.
    
    This is not a true vector database (no dense embeddings), but provides
    a functional keyword-based semantic retrieval mechanism out of the box.
    """

    def __init__(self, persist_path: Optional[str] = None):
        self.persist_path = persist_path
        self.items: Dict[str, MemoryItem] = {}
        # Document frequencies for words
        self.df: Dict[str, int] = collections.defaultdict(int)
        self.total_docs = 0
        
        if self.persist_path and os.path.exists(self.persist_path):
            self._load()

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenizer."""
        return "".join(c if c.isalnum() else " " for c in text.lower()).split()

    def add(self, item: MemoryItem) -> None:
        if item.id in self.items:
            self.remove(item.id)
            
        self.items[item.id] = item
        self.total_docs += 1
        
        # Update document frequencies
        unique_tokens = set(self._tokenize(item.content))
        for t in unique_tokens:
            self.df[t] += 1
            
        self._save()

    def remove(self, item_id: str) -> bool:
        if item_id not in self.items:
            return False
            
        item = self.items.pop(item_id)
        self.total_docs -= 1
        
        # We don't bother decrementing DF perfectly for this lightweight fallback,
        # but in a real implementation we might.
        
        self._save()
        return True

    def clear(self) -> None:
        self.items.clear()
        self.df.clear()
        self.total_docs = 0
        self._save()

    def search(self, query: str, limit: int = 5) -> List[tuple[MemoryItem, float]]:
        if not self.items:
            return []
            
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
            
        # Calculate scores using a simplified TF-IDF
        scores: Dict[str, float] = collections.defaultdict(float)
        
        for q_token in query_tokens:
            if q_token not in self.df:
                continue
                
            # Inverse Document Frequency
            idf = math.log((self.total_docs + 1) / (self.df[q_token] + 1)) + 1
            
            for doc_id, item in self.items.items():
                doc_tokens = self._tokenize(item.content)
                # Term Frequency
                tf = doc_tokens.count(q_token) / max(1, len(doc_tokens))
                scores[doc_id] += tf * idf

        # Normalize scores to 0-1 range roughly
        max_score = max(scores.values()) if scores else 1.0
        
        results = []
        for doc_id, score in scores.items():
            if score > 0:
                normalized = min(1.0, score / max_score)
                results.append((self.items[doc_id], normalized))
                
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def _save(self) -> None:
        if not self.persist_path:
            return
        try:
            os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
            data = {
                "items": {k: v.to_dict() for k, v in self.items.items()},
                "df": dict(self.df),
                "total_docs": self.total_docs
            }
            with open(self.persist_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to save TFIDF store: {e}")

    def _load(self) -> None:
        try:
            with open(self.persist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.total_docs = data.get("total_docs", 0)
            self.df = collections.defaultdict(int, data.get("df", {}))
            
            for k, v in data.get("items", {}).items():
                self.items[k] = MemoryItem.from_dict(v)
        except Exception as e:
            logger.error(f"Failed to load TFIDF store: {e}")
