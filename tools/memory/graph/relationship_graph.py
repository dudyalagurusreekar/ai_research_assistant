"""Semantic Relationship Graph for linking and traversing memory connections."""

from typing import List, Dict, Set
from tools.memory.interfaces.memory_interfaces import IRelationshipGraph
from tools.memory.models.memory_models import MemoryLink
from infrastructure.logging.logger import StructuredLogger


class RelationshipGraph(IRelationshipGraph):
    """Manages semantic memory relationships and graph traversal."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("RelationshipGraph")
        self._links: Dict[str, MemoryLink] = {}
        self._adj: Dict[str, List[MemoryLink]] = {}

    async def add_link(self, link: MemoryLink) -> None:
        """Add semantic relationship link between two memory items."""
        self._links[link.link_id] = link
        
        # Bi-directional graph indexing
        self._adj.setdefault(link.source_memory_id, []).append(link)
        self._adj.setdefault(link.target_memory_id, []).append(link)
        self._logger.debug(f"Added link '{link.link_id}': {link.source_memory_id} --({link.relationship_type})--> {link.target_memory_id}")

    async def get_links_for_memory(self, memory_id: str) -> List[MemoryLink]:
        """Retrieve all links associated with memory_id."""
        return self._adj.get(memory_id, [])

    async def get_related_memories(self, memory_id: str, depth: int = 1) -> List[str]:
        """Graph BFS traversal returning related memory IDs up to depth N."""
        visited: Set[str] = {memory_id}
        queue: List[tuple[str, int]] = [(memory_id, 0)]

        while queue:
            curr_id, curr_depth = queue.pop(0)
            if curr_depth >= depth:
                continue

            for link in self._adj.get(curr_id, []):
                next_id = link.target_memory_id if link.source_memory_id == curr_id else link.source_memory_id
                if next_id not in visited:
                    visited.add(next_id)
                    queue.append((next_id, curr_depth + 1))

        visited.remove(memory_id)
        return list(visited)
