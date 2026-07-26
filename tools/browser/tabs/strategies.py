"""Tab Management Strategies.

Defines abstract and concrete strategies for tab lifecycle policies:
how many tabs to allow, when to evict, and how to select tabs for reuse.
"""

import abc
import logging
from typing import Dict, List, Optional

from tools.browser.tabs.models import TabInfo

logger = logging.getLogger("TabStrategies")


class TabStrategy(abc.ABC):
    """Abstract base class for tab management policies.

    Strategies control how the coordinator manages tab limits,
    eviction, and reuse decisions. Different task types benefit from
    different strategies (e.g., research tasks need parallel tabs,
    form tasks need conservative reuse).
    """

    @abc.abstractmethod
    def should_evict(self, tabs: Dict[str, TabInfo]) -> Optional[str]:
        """Determine if a tab should be evicted to make room for a new one.

        Args:
            tabs: Current tab registry mapping tab_id → TabInfo.

        Returns:
            Optional[str]: The tab_id to evict, or None if no eviction is needed.
        """
        pass

    @abc.abstractmethod
    def should_reuse_tab(
        self, tabs: Dict[str, TabInfo], target_url: str
    ) -> Optional[str]:
        """Determine if an existing tab should be reused for a new navigation.

        Args:
            tabs: Current tab registry.
            target_url: URL that needs to be loaded.

        Returns:
            Optional[str]: The tab_id to reuse, or None if a new tab should be opened.
        """
        pass

    @property
    @abc.abstractmethod
    def max_tabs(self) -> int:
        """Maximum number of concurrent tabs allowed by this strategy.

        Returns:
            int: Tab limit.
        """
        pass


class ConservativeStrategy(TabStrategy):
    """Conservative tab management: aggressively reuse tabs, low limit.

    Best for sequential workflows where memory conservation is important.
    Keeps a maximum of 3 tabs open and prefers to navigate existing tabs
    rather than opening new ones.

    Eviction policy: Least Recently Used (LRU).
    Reuse policy: Reuse any non-active tab, preferring tabs with matching domains.
    """

    def __init__(self, max_tab_count: int = 3) -> None:
        """Initialize conservative strategy.

        Args:
            max_tab_count: Maximum concurrent tabs. Default 3.
        """
        self._max_tabs = max_tab_count

    @property
    def max_tabs(self) -> int:
        """Maximum tabs allowed."""
        return self._max_tabs

    def should_evict(self, tabs: Dict[str, TabInfo]) -> Optional[str]:
        """Evict the least recently used non-active tab if at capacity.

        Args:
            tabs: Current tab registry.

        Returns:
            Optional[str]: Tab ID to evict, or None.
        """
        if len(tabs) < self._max_tabs:
            return None

        # Find non-active tabs sorted by last_accessed (oldest first)
        candidates = [
            (tid, info) for tid, info in tabs.items() if not info.is_active
        ]
        if not candidates:
            return None

        candidates.sort(key=lambda x: x[1].last_accessed)
        return candidates[0][0]

    def should_reuse_tab(
        self, tabs: Dict[str, TabInfo], target_url: str
    ) -> Optional[str]:
        """Try to reuse an existing tab, preferring domain matches.

        Args:
            tabs: Current tab registry.
            target_url: Target URL.

        Returns:
            Optional[str]: Tab ID to reuse, or None.
        """
        if not tabs:
            return None

        # Extract domain from target URL
        target_domain = self._extract_domain(target_url)

        # First: check for exact URL match (no navigation needed)
        for tid, info in tabs.items():
            if info.url == target_url:
                return tid

        # Second: check for same-domain non-active tabs
        domain_matches = []
        for tid, info in tabs.items():
            if not info.is_active and self._extract_domain(info.url) == target_domain:
                domain_matches.append((tid, info))

        if domain_matches:
            # Prefer least recently used domain-matching tab
            domain_matches.sort(key=lambda x: x[1].last_accessed)
            return domain_matches[0][0]

        # Third: reuse any non-active tab (LRU) if at capacity
        if len(tabs) >= self._max_tabs:
            non_active = [
                (tid, info) for tid, info in tabs.items() if not info.is_active
            ]
            if non_active:
                non_active.sort(key=lambda x: x[1].last_accessed)
                return non_active[0][0]

        return None

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from a URL string.

        Args:
            url: URL to extract domain from.

        Returns:
            str: Domain string, or empty if extraction fails.
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ""


class ParallelStrategy(TabStrategy):
    """Parallel tab management: open tabs freely for concurrent extraction.

    Best for research and data gathering workflows where multiple pages
    need to be open simultaneously for cross-referencing.

    Eviction policy: LRU, but only when hard limit is reached.
    Reuse policy: Only reuse tabs with exact URL matches.
    """

    def __init__(self, max_tab_count: int = 8) -> None:
        """Initialize parallel strategy.

        Args:
            max_tab_count: Maximum concurrent tabs. Default 8.
        """
        self._max_tabs = max_tab_count

    @property
    def max_tabs(self) -> int:
        """Maximum tabs allowed."""
        return self._max_tabs

    def should_evict(self, tabs: Dict[str, TabInfo]) -> Optional[str]:
        """Evict only when hard limit is reached.

        Args:
            tabs: Current tab registry.

        Returns:
            Optional[str]: Tab ID to evict, or None.
        """
        if len(tabs) < self._max_tabs:
            return None

        # LRU eviction of non-active tabs
        candidates = [
            (tid, info) for tid, info in tabs.items() if not info.is_active
        ]
        if not candidates:
            return None

        candidates.sort(key=lambda x: x[1].last_accessed)
        return candidates[0][0]

    def should_reuse_tab(
        self, tabs: Dict[str, TabInfo], target_url: str
    ) -> Optional[str]:
        """Only reuse tabs with exact URL matches.

        Args:
            tabs: Current tab registry.
            target_url: Target URL.

        Returns:
            Optional[str]: Tab ID with exact URL match, or None.
        """
        for tid, info in tabs.items():
            if info.url == target_url:
                return tid
        return None
