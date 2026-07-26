"""Multi-Tab Coordinator Data Models.

Defines data structures for tab tracking, tab groups, and tab lifecycle events.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class TabEvent(str, Enum):
    """Lifecycle events for browser tab tracking.

    Events:
        OPENED: A new tab was created.
        CLOSED: A tab was closed.
        SWITCHED: The active tab changed.
        NAVIGATED: A tab navigated to a new URL.
        POPUP: A popup/new window was detected and captured.
        EVICTED: A tab was closed due to resource limits (LRU eviction).
    """

    OPENED = "OPENED"
    CLOSED = "CLOSED"
    SWITCHED = "SWITCHED"
    NAVIGATED = "NAVIGATED"
    POPUP = "POPUP"
    EVICTED = "EVICTED"


@dataclass
class TabInfo:
    """Tracking information for a single browser tab.

    Attributes:
        tab_id: Unique identifier for this tab.
        url: Current URL loaded in the tab.
        title: Current page title.
        is_active: Whether this is the currently focused tab.
        created_at: Unix timestamp when the tab was created.
        last_accessed: Unix timestamp of the most recent interaction.
        navigation_count: Number of navigations performed in this tab.
        group_name: Optional name of the tab group this belongs to.
        metadata: Optional arbitrary metadata associated with the tab.
    """

    tab_id: str = field(default_factory=lambda: f"tab_{uuid.uuid4().hex[:8]}")
    url: str = "about:blank"
    title: str = ""
    is_active: bool = False
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    navigation_count: int = 0
    group_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        """Update the last_accessed timestamp to now."""
        self.last_accessed = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize tab info to a JSON-compatible dictionary."""
        return {
            "tab_id": self.tab_id,
            "url": self.url,
            "title": self.title,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "navigation_count": self.navigation_count,
            "group_name": self.group_name,
            "metadata": self.metadata,
        }


@dataclass
class TabGroup:
    """Named group of related browser tabs.

    Used to organize tabs that belong to the same task or workflow,
    such as "research tabs" or "form submission tabs".

    Attributes:
        name: Human-readable group name.
        tab_ids: List of tab IDs belonging to this group.
        created_at: Unix timestamp when the group was created.
        purpose: Description of why these tabs are grouped.
    """

    name: str = ""
    tab_ids: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    purpose: str = ""

    def add_tab(self, tab_id: str) -> None:
        """Add a tab to this group.

        Args:
            tab_id: Tab identifier to add.
        """
        if tab_id not in self.tab_ids:
            self.tab_ids.append(tab_id)

    def remove_tab(self, tab_id: str) -> None:
        """Remove a tab from this group.

        Args:
            tab_id: Tab identifier to remove.
        """
        if tab_id in self.tab_ids:
            self.tab_ids.remove(tab_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize tab group to a JSON-compatible dictionary."""
        return {
            "name": self.name,
            "tab_ids": self.tab_ids,
            "created_at": self.created_at,
            "purpose": self.purpose,
            "tab_count": len(self.tab_ids),
        }


@dataclass
class TabEventRecord:
    """Timestamped record of a tab lifecycle event.

    Used for auditing, debugging, and replaying tab management decisions.

    Attributes:
        event: The type of tab event.
        tab_id: Tab that the event relates to.
        timestamp: Unix timestamp of the event.
        details: Additional event-specific information.
    """

    event: TabEvent = TabEvent.OPENED
    tab_id: str = ""
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event record to dictionary."""
        return {
            "event": self.event.value,
            "tab_id": self.tab_id,
            "timestamp": self.timestamp,
            "details": self.details,
        }
