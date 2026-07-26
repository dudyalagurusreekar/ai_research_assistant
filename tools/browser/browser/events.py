"""Event-Driven Browser State Notifications.

Provides event types, data structures, and an event dispatcher for browser state changes,
allowing components (context manager, monitor, planner) to react to DOM, URL, or Tab changes
without polling.
"""

from enum import Enum
from typing import Callable, Dict, Any, List, Optional
from dataclasses import dataclass, field
import time
import logging

logger = logging.getLogger("BrowserEventDispatcher")


class BrowserEventType(str, Enum):
    """Types of browser state events emitted during execution."""

    URL_CHANGED = "URL_CHANGED"
    TITLE_CHANGED = "TITLE_CHANGED"
    DOM_CHANGED = "DOM_CHANGED"
    TABS_CHANGED = "TABS_CHANGED"
    COOKIES_CHANGED = "COOKIES_CHANGED"
    STORAGE_CHANGED = "STORAGE_CHANGED"
    SCROLL_CHANGED = "SCROLL_CHANGED"
    STATE_UPDATED = "STATE_UPDATED"
    STATE_ROLLED_BACK = "STATE_ROLLED_BACK"


@dataclass
class BrowserEvent:
    """Immutable event record representing a change in browser state."""

    event_type: BrowserEventType
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    old_value: Any = None
    new_value: Any = None


EventListener = Callable[[BrowserEvent], None]


class EventDispatcher:
    """Dispatches browser state events to registered subscribers."""

    def __init__(self) -> None:
        self._listeners: Dict[BrowserEventType, List[EventListener]] = {
            event_type: [] for event_type in BrowserEventType
        }
        self._global_listeners: List[EventListener] = []

    def subscribe(self, listener: EventListener, event_type: Optional[BrowserEventType] = None) -> None:
        """Subscribe a listener to a specific event type or to all events if event_type is None."""
        if event_type is None:
            if listener not in self._global_listeners:
                self._global_listeners.append(listener)
        else:
            if listener not in self._listeners[event_type]:
                self._listeners[event_type].append(listener)

    def unsubscribe(self, listener: EventListener, event_type: Optional[BrowserEventType] = None) -> None:
        """Unsubscribe a listener from an event type or from global listeners."""
        if event_type is None:
            if listener in self._global_listeners:
                self._global_listeners.remove(listener)
        else:
            if listener in self._listeners[event_type]:
                self._listeners[event_type].remove(listener)

    def dispatch(self, event: BrowserEvent) -> None:
        """Dispatch an event to all matching listeners."""
        for listener in list(self._listeners.get(event.event_type, [])):
            try:
                listener(event)
            except Exception as e:
                logger.debug(f"Error in event listener for {event.event_type}: {e}")

        for listener in list(self._global_listeners):
            try:
                listener(event)
            except Exception as e:
                logger.debug(f"Error in global event listener: {e}")

    def clear_listeners(self) -> None:
        """Remove all registered listeners."""
        for event_type in self._listeners:
            self._listeners[event_type].clear()
        self._global_listeners.clear()
