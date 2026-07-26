"""Browser Execution & State Layer (`tools/browser/browser/`).

Provides deterministic browser automation execution and an Event-Driven single source of truth
for runtime state (`BrowserState`), keeping browser mechanics cleanly decoupled from LLM reasoning.
"""

from tools.browser.browser.events import (
    BrowserEvent,
    BrowserEventType,
    EventDispatcher,
    EventListener,
)
from tools.browser.browser.state import (
    BrowserState,
    BrowserStateSnapshot,
)
from tools.browser.browser.tool import (
    BrowserToolFacade,
)

__all__ = [
    "BrowserEvent",
    "BrowserEventType",
    "EventDispatcher",
    "EventListener",
    "BrowserState",
    "BrowserStateSnapshot",
    "BrowserToolFacade",
]
