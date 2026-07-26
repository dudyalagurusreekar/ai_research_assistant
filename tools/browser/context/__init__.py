"""Context Management Layer (`tools/browser/context/`).

Provides minimal prompt building, history summarization, payload offloading, and DOM pruning
to optimize token usage and latency during browser task execution.
"""

from tools.browser.context.manager import (
    ContextLifecycleManager,
    ContextManager,
)
from tools.browser.context.pruner import (
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
