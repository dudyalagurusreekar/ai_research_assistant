"""Abstract interface contracts for the Memory Platform."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from tools.memory.models.memory_models import (
    MemoryItem,
    MemoryType,
    MemoryLink,
    MemoryQuery,
    MemorySearchResult,
    MemoryConsolidationResult,
)


class IMemoryProvider(ABC):
    """Abstract interface for domain-specific memory storage providers."""

    @property
    @abstractmethod
    def memory_type(self) -> MemoryType:
        """Memory type handled by this provider."""
        pass

    @abstractmethod
    async def store(self, item: MemoryItem) -> str:
        """Store a memory item and return memory_id."""
        pass

    @abstractmethod
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a specific memory item by ID."""
        pass

    @abstractmethod
    async def query(self, memory_query: MemoryQuery) -> List[MemoryItem]:
        """Query memory items matching conditions."""
        pass

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory item."""
        pass

    @abstractmethod
    async def list_all(self) -> List[MemoryItem]:
        """List all items in this provider."""
        pass


class IMemoryRegistry(ABC):
    """Abstract interface for memory provider registry."""

    @abstractmethod
    def register(self, provider: IMemoryProvider) -> None:
        """Register a memory provider strategy."""
        pass

    @abstractmethod
    def get_provider(self, memory_type: MemoryType) -> Optional[IMemoryProvider]:
        """Get provider by MemoryType."""
        pass

    @abstractmethod
    def list_providers(self) -> List[IMemoryProvider]:
        """List all registered providers."""
        pass


class IMemoryIndex(ABC):
    """Abstract memory search index interface."""

    @abstractmethod
    async def index_memory(self, item: MemoryItem) -> None:
        """Index a memory item."""
        pass

    @abstractmethod
    async def remove_from_index(self, memory_id: str) -> None:
        """Remove memory item from index."""
        pass

    @abstractmethod
    async def search(self, query: MemoryQuery) -> List[MemoryItem]:
        """Search indexed memories."""
        pass


class IRelationshipGraph(ABC):
    """Abstract semantic memory relationship graph interface."""

    @abstractmethod
    async def add_link(self, link: MemoryLink) -> None:
        """Add a semantic relationship link between memories."""
        pass

    @abstractmethod
    async def get_links_for_memory(self, memory_id: str) -> List[MemoryLink]:
        """Retrieve all links associated with a memory item."""
        pass

    @abstractmethod
    async def get_related_memories(self, memory_id: str, depth: int = 1) -> List[str]:
        """Get IDs of related memory items up to a given depth."""
        pass


class IMemoryConsolidator(ABC):
    """Abstract memory consolidation and decay interface."""

    @abstractmethod
    async def consolidate(self, providers: List[IMemoryProvider]) -> MemoryConsolidationResult:
        """Run memory consolidation, decay importance, and transfer items."""
        pass


class IMemoryManager(ABC):
    """Abstract central memory manager interface."""

    @abstractmethod
    async def store_memory(self, content: str, memory_type: MemoryType = MemoryType.SHORT_TERM, **kwargs) -> MemoryItem:
        """Store a new memory item."""
        pass

    @abstractmethod
    async def recall(self, query_text: str, **kwargs) -> MemorySearchResult:
        """Recall memory items matching query."""
        pass

    @abstractmethod
    async def link_memories(self, source_id: str, target_id: str, relationship_type: str = "relates_to") -> MemoryLink:
        """Link two memory items semantically."""
        pass
