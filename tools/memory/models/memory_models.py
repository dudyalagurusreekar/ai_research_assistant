"""Data models for the Memory Platform."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from core.utils.id_generator import generate_id
from core.utils.time_utils import utc_now, utc_isoformat


class MemoryType(str, Enum):
    """Categorization of memory storage domains."""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    SESSION = "session"
    WORKING = "working"
    KNOWLEDGE = "knowledge"


@dataclass
class MemoryLink:
    """Semantic relationship link connecting two memory items."""
    link_id: str = field(default_factory=lambda: generate_id("lnk_"))
    source_memory_id: str = ""
    target_memory_id: str = ""
    relationship_type: str = "relates_to"  # e.g., 'derived_from', 'supports', 'refutes', 'part_of'
    weight: float = 1.0
    created_at: str = field(default_factory=utc_isoformat)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "link_id": self.link_id,
            "source_memory_id": self.source_memory_id,
            "target_memory_id": self.target_memory_id,
            "relationship_type": self.relationship_type,
            "weight": self.weight,
            "created_at": self.created_at,
        }


@dataclass
class MemoryItem:
    """Unified container representing a single memory record."""
    memory_id: str = field(default_factory=lambda: generate_id("mem_"))
    memory_type: MemoryType = MemoryType.SHORT_TERM
    content: str = ""
    summary: Optional[str] = None
    source: str = "user"  # 'user', 'browser', 'document', 'search', 'tool'
    importance: float = 1.0  # 0.0 to 1.0
    access_count: int = 0
    tags: List[str] = field(default_factory=list)
    links: List[MemoryLink] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_isoformat)
    updated_at: str = field(default_factory=utc_isoformat)
    last_accessed_at: str = field(default_factory=utc_isoformat)

    def touch(self) -> None:
        """Update access count and last_accessed timestamp."""
        self.access_count += 1
        self.last_accessed_at = utc_isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "summary": self.summary,
            "source": self.source,
            "importance": self.importance,
            "access_count": self.access_count,
            "tags": self.tags,
            "links": [l.to_dict() for l in self.links],
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_accessed_at": self.last_accessed_at,
        }


@dataclass
class MemoryQuery:
    """Standardized search query for memory retrieval."""
    query_text: str = ""
    memory_types: List[MemoryType] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    min_importance: float = 0.0
    max_results: int = 10
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_text": self.query_text,
            "memory_types": [mt.value for mt in self.memory_types],
            "tags": self.tags,
            "min_importance": self.min_importance,
            "max_results": self.max_results,
            "session_id": self.session_id,
        }


@dataclass
class MemorySearchResult:
    """Container for recalled memory search results."""
    query: MemoryQuery
    memories: List[MemoryItem] = field(default_factory=list)
    relevance_scores: Dict[str, float] = field(default_factory=dict)
    total_found: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query.to_dict(),
            "memories": [m.to_dict() for m in self.memories],
            "relevance_scores": self.relevance_scores,
            "total_found": self.total_found,
        }


@dataclass
class MemoryConsolidationResult:
    """Summary metrics of a memory consolidation cycle."""
    consolidated_count: int = 0
    pruned_count: int = 0
    decayed_count: int = 0
    summarized_count: int = 0
    timestamp: str = field(default_factory=utc_isoformat)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "consolidated_count": self.consolidated_count,
            "pruned_count": self.pruned_count,
            "decayed_count": self.decayed_count,
            "summarized_count": self.summarized_count,
            "timestamp": self.timestamp,
        }
