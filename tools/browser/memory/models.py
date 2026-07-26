"""Core data models for the Agent Memory & Knowledge System."""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional


class MemoryType(str, Enum):
    """Classification of memory items by layer."""
    WORKING = "WORKING"
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"
    PROCEDURAL = "PROCEDURAL"


@dataclass
class RelevanceScore:
    """Calculated score for a retrieved memory."""
    semantic_similarity: float = 0.0
    recency_weight: float = 0.0
    importance_weight: float = 0.0
    final_score: float = 0.0


@dataclass
class MemoryItem:
    """A single discrete unit of memory."""
    content: str
    memory_type: MemoryType
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    importance: float = 1.0  # 0.0 to 1.0, how critical this memory is
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Embeddings can be optionally stored if a vector db is present
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "importance": self.importance,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        item = cls(
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            id=data.get("id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", time.time()),
            last_accessed=data.get("last_accessed", time.time()),
            access_count=data.get("access_count", 0),
            importance=data.get("importance", 1.0),
            metadata=data.get("metadata", {}),
        )
        return item

    def touch(self) -> None:
        """Update access stats."""
        self.last_accessed = time.time()
        self.access_count += 1
