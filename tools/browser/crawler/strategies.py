"""Graph Traversal Strategy implementations for the Web Crawling Subsystem.

This module provides the Strategy Pattern interface `TraversalStrategy` along with
concrete strategies `BFSTraversal` (Breadth-First Search) and `DFSTraversal` (Depth-First Search).
"""

from abc import ABC, abstractmethod
from collections import deque
from typing import Optional, Tuple


class TraversalStrategy(ABC):
    """Abstract interface defining the contract for graph traversal strategies."""

    @abstractmethod
    def add_url(self, url: str, depth: int, parent_url: Optional[str] = None) -> None:
        """Add a candidate URL node to the traversal queue/stack.

        Args:
            url (str): Target URL string.
            depth (int): Depth level.
            parent_url (Optional[str]): Parent URL that referenced this node.
        """

    @abstractmethod
    def pop_url(self) -> Optional[Tuple[str, int, Optional[str]]]:
        """Pop the next URL node to crawl.

        Returns:
            Optional[Tuple[str, int, Optional[str]]]: (url, depth, parent_url) tuple or None if empty.
        """

    @abstractmethod
    def has_urls(self) -> bool:
        """Check if traversal queue/stack contains pending URLs.

        Returns:
            bool: True if pending URLs remain.
        """


class BFSTraversal(TraversalStrategy):
    """Breadth-First Search (BFS) graph traversal strategy using a FIFO Queue.

    Explores all sibling links at the current depth before descending deeper.
    Ideal for broad domain exploration and discovering site structure.
    """

    def __init__(self) -> None:
        self._queue: deque = deque()

    def add_url(self, url: str, depth: int, parent_url: Optional[str] = None) -> None:
        self._queue.append((url, depth, parent_url))

    def pop_url(self) -> Optional[Tuple[str, int, Optional[str]]]:
        if self._queue:
            return self._queue.popleft()
        return None

    def has_urls(self) -> bool:
        return bool(self._queue)


class DFSTraversal(TraversalStrategy):
    """Depth-First Search (DFS) graph traversal strategy using a LIFO Stack.

    Descends as deep as possible along a single link path before backtracking.
    Ideal for deep topic exploration and long-form document reading.
    """

    def __init__(self) -> None:
        self._stack: list = []

    def add_url(self, url: str, depth: int, parent_url: Optional[str] = None) -> None:
        self._stack.append((url, depth, parent_url))

    def pop_url(self) -> Optional[Tuple[str, int, Optional[str]]]:
        if self._stack:
            return self._stack.pop()
        return None

    def has_urls(self) -> bool:
        return bool(self._stack)
