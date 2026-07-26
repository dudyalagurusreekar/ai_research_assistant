"""BrowserState - Event-Driven Single Source of Truth for Browser State.

This module provides the central state holder and snapshot representation for the browser execution layer.
It tracks URL, title, DOM snapshot, tabs, cookies, storage, scroll position, and navigation history,
emitting granular event notifications when state properties change so other components
(context manager, monitor, planner) can react without polling.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import time
import logging

from tools.browser.browser.events import (
    BrowserEvent,
    BrowserEventType,
    EventDispatcher,
    EventListener,
)

logger = logging.getLogger("BrowserState")


@dataclass
class BrowserStateSnapshot:
    """Immutable representation of the browser state at a specific action step."""

    version: int
    timestamp: float
    url: str
    title: str
    dom_snapshot: str
    tabs: List[str] = field(default_factory=list)
    active_tab_index: int = 0
    cookies: List[Dict[str, Any]] = field(default_factory=list)
    local_storage: Dict[str, str] = field(default_factory=dict)
    session_storage: Dict[str, str] = field(default_factory=dict)
    scroll_position: Dict[str, int] = field(default_factory=dict)
    focused_element_selector: Optional[str] = None
    detected_forms: List[Dict[str, Any]] = field(default_factory=list)
    previous_action: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to JSON-serializable dictionary."""
        return {
            "version": self.version,
            "timestamp": self.timestamp,
            "url": self.url,
            "title": self.title,
            "dom_snapshot": self.dom_snapshot,
            "tabs": self.tabs,
            "active_tab_index": self.active_tab_index,
            "cookies": self.cookies,
            "local_storage": self.local_storage,
            "session_storage": self.session_storage,
            "scroll_position": self.scroll_position,
            "focused_element_selector": self.focused_element_selector,
            "detected_forms": self.detected_forms,
            "previous_action": self.previous_action,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BrowserStateSnapshot":
        """Reconstruct snapshot from dictionary."""
        return cls(
            version=data["version"],
            timestamp=data["timestamp"],
            url=data["url"],
            title=data["title"],
            dom_snapshot=data["dom_snapshot"],
            tabs=data.get("tabs", []),
            active_tab_index=data.get("active_tab_index", 0),
            cookies=data.get("cookies", []),
            local_storage=data.get("local_storage", {}),
            session_storage=data.get("session_storage", {}),
            scroll_position=data.get("scroll_position", {}),
            focused_element_selector=data.get("focused_element_selector"),
            detected_forms=data.get("detected_forms", []),
            previous_action=data.get("previous_action"),
        )


class BrowserState:
    """Event-driven single source of truth for the browser's runtime state.

    Maintains current URL, title, DOM snapshot, open tabs, cookies, local/session storage,
    scroll position, and navigation history. Emits events via an EventDispatcher whenever
    state mutates.
    """

    def __init__(self, dispatcher: Optional[EventDispatcher] = None) -> None:
        """Initialize the browser state.

        Args:
            dispatcher (Optional[EventDispatcher]): Custom event dispatcher instance.
                If None, creates a new default EventDispatcher.
        """
        self.dispatcher = dispatcher or EventDispatcher()

        # Core runtime state
        self.version: int = 0
        self.url: str = "about:blank"
        self.title: str = ""
        self.dom_snapshot: str = ""
        self.tabs: List[str] = []
        self.active_tab_index: int = 0
        self.cookies: List[Dict[str, Any]] = []
        self.local_storage: Dict[str, str] = {}
        self.session_storage: Dict[str, str] = {}
        self.scroll_position: Dict[str, int] = {"x": 0, "y": 0}
        self.focused_element_selector: Optional[str] = None
        self.detected_forms: List[Dict[str, Any]] = []
        self.previous_action: Optional[Dict[str, Any]] = None

        # Persistent session metadata
        self.navigation_history: List[str] = []
        self.screenshots: List[str] = []
        self.downloaded_files: List[str] = []
        self.extracted_data: List[Dict[str, Any]] = []

    def subscribe(self, listener: EventListener, event_type: Optional[BrowserEventType] = None) -> None:
        """Subscribe a callback to browser state events."""
        self.dispatcher.subscribe(listener, event_type)

    def unsubscribe(self, listener: EventListener, event_type: Optional[BrowserEventType] = None) -> None:
        """Unsubscribe a callback from browser state events."""
        self.dispatcher.unsubscribe(listener, event_type)

    def update_state(
        self, snapshot: BrowserStateSnapshot, previous_action: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update current browser state from a new snapshot and dispatch change events.

        Args:
            snapshot (BrowserStateSnapshot): Newly captured state snapshot.
            previous_action (Optional[Dict[str, Any]]): Action that led to this state change.
        """
        old_url = self.url
        old_title = self.title
        old_dom = self.dom_snapshot
        old_tabs = list(self.tabs)
        old_cookies = list(self.cookies)
        old_local_storage = dict(self.local_storage)
        old_session_storage = dict(self.session_storage)
        old_scroll = dict(self.scroll_position)

        # Update properties
        self.version = snapshot.version
        self.url = snapshot.url
        self.title = snapshot.title
        self.dom_snapshot = snapshot.dom_snapshot
        self.tabs = list(snapshot.tabs)
        self.active_tab_index = snapshot.active_tab_index
        self.cookies = list(snapshot.cookies)
        self.local_storage = dict(snapshot.local_storage)
        self.session_storage = dict(snapshot.session_storage)
        self.scroll_position = dict(snapshot.scroll_position)
        self.focused_element_selector = snapshot.focused_element_selector
        self.detected_forms = list(snapshot.detected_forms)
        self.previous_action = previous_action or snapshot.previous_action

        # Update navigation history
        if not self.navigation_history or self.navigation_history[-1] != self.url:
            self.navigation_history.append(self.url)

        # Dispatch URL change event
        if old_url != self.url:
            self.dispatcher.dispatch(
                BrowserEvent(
                    event_type=BrowserEventType.URL_CHANGED,
                    old_value=old_url,
                    new_value=self.url,
                    data={"url": self.url, "title": self.title},
                )
            )

        # Dispatch Title change event
        if old_title != self.title:
            self.dispatcher.dispatch(
                BrowserEvent(
                    event_type=BrowserEventType.TITLE_CHANGED,
                    old_value=old_title,
                    new_value=self.title,
                    data={"title": self.title},
                )
            )

        # Dispatch DOM change event
        if old_dom != self.dom_snapshot:
            self.dispatcher.dispatch(
                BrowserEvent(
                    event_type=BrowserEventType.DOM_CHANGED,
                    old_value=old_dom,
                    new_value=self.dom_snapshot,
                    data={"url": self.url, "dom_length": len(self.dom_snapshot)},
                )
            )

        # Dispatch Tabs change event
        if old_tabs != self.tabs:
            self.dispatcher.dispatch(
                BrowserEvent(
                    event_type=BrowserEventType.TABS_CHANGED,
                    old_value=old_tabs,
                    new_value=self.tabs,
                    data={"tabs": self.tabs, "active_tab_index": self.active_tab_index},
                )
            )

        # Dispatch Cookies change event
        if old_cookies != self.cookies:
            self.dispatcher.dispatch(
                BrowserEvent(
                    event_type=BrowserEventType.COOKIES_CHANGED,
                    old_value=old_cookies,
                    new_value=self.cookies,
                    data={"cookies_count": len(self.cookies)},
                )
            )

        # Dispatch Storage change event
        if old_local_storage != self.local_storage or old_session_storage != self.session_storage:
            self.dispatcher.dispatch(
                BrowserEvent(
                    event_type=BrowserEventType.STORAGE_CHANGED,
                    old_value={"local": old_local_storage, "session": old_session_storage},
                    new_value={"local": self.local_storage, "session": self.session_storage},
                    data={
                        "local_storage": self.local_storage,
                        "session_storage": self.session_storage,
                    },
                )
            )

        # Dispatch Scroll change event
        if old_scroll != self.scroll_position:
            self.dispatcher.dispatch(
                BrowserEvent(
                    event_type=BrowserEventType.SCROLL_CHANGED,
                    old_value=old_scroll,
                    new_value=self.scroll_position,
                    data={"scroll_position": self.scroll_position},
                )
            )

        # Dispatch general State Updated event
        self.dispatcher.dispatch(
            BrowserEvent(
                event_type=BrowserEventType.STATE_UPDATED,
                new_value=self.get_current_snapshot(),
                data={"version": self.version, "url": self.url},
            )
        )

    def rollback_state(self, snapshot: BrowserStateSnapshot) -> None:
        """Rollback current state to match an earlier snapshot and emit rollback event.

        Args:
            snapshot (BrowserStateSnapshot): Target snapshot to restore.
        """
        old_version = self.version
        self.version = snapshot.version
        self.url = snapshot.url
        self.title = snapshot.title
        self.dom_snapshot = snapshot.dom_snapshot
        self.tabs = list(snapshot.tabs)
        self.active_tab_index = snapshot.active_tab_index
        self.cookies = list(snapshot.cookies)
        self.local_storage = dict(snapshot.local_storage)
        self.session_storage = dict(snapshot.session_storage)
        self.scroll_position = dict(snapshot.scroll_position)
        self.focused_element_selector = snapshot.focused_element_selector
        self.detected_forms = list(snapshot.detected_forms)
        self.previous_action = snapshot.previous_action

        self.dispatcher.dispatch(
            BrowserEvent(
                event_type=BrowserEventType.STATE_ROLLED_BACK,
                old_value=old_version,
                new_value=self.version,
                data={"version": self.version, "url": self.url},
            )
        )

    def get_current_snapshot(self) -> BrowserStateSnapshot:
        """Create and return an immutable snapshot of the current state."""
        return BrowserStateSnapshot(
            version=self.version,
            timestamp=time.time(),
            url=self.url,
            title=self.title,
            dom_snapshot=self.dom_snapshot,
            tabs=list(self.tabs),
            active_tab_index=self.active_tab_index,
            cookies=list(self.cookies),
            local_storage=dict(self.local_storage),
            session_storage=dict(self.session_storage),
            scroll_position=dict(self.scroll_position),
            focused_element_selector=self.focused_element_selector,
            detected_forms=list(self.detected_forms),
            previous_action=self.previous_action,
        )

    def record_screenshot(self, filepath: str) -> None:
        """Record a screenshot artifact path."""
        if filepath and filepath not in self.screenshots:
            self.screenshots.append(filepath)

    def record_download(self, filepath: str) -> None:
        """Record a downloaded file path."""
        if filepath and filepath not in self.downloaded_files:
            self.downloaded_files.append(filepath)

    def record_extracted_data(self, key: str, value: Any) -> None:
        """Record extracted data field."""
        self.extracted_data.append({
            "key": key,
            "value": value,
            "timestamp": time.time(),
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to a JSON-serializable dictionary."""
        return {
            "version": self.version,
            "url": self.url,
            "title": self.title,
            "tabs": self.tabs,
            "active_tab_index": self.active_tab_index,
            "scroll_position": self.scroll_position,
            "focused_element_selector": self.focused_element_selector,
            "navigation_history": self.navigation_history,
            "screenshots": self.screenshots,
            "downloaded_files": self.downloaded_files,
            "extracted_data": self.extracted_data,
        }
