"""Context Lifecycle Manager Legacy Wrapper.

Re-exports ContextLifecycleManager and ContextManager from `tools.browser.context`
for backwards compatibility with existing imports.
"""

from tools.browser.context import (
    ContextLifecycleManager,
    ContextManager,
    DOMPruner,
    PrunedDOM,
    PrunedElement,
)

__all__ = [
    "ContextLifecycleManager",
    "ContextManager",
    "DOMPruner",
    "PrunedDOM",
    "PrunedElement",
]
