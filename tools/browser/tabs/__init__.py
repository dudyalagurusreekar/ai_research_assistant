"""Multi-Tab Coordinator Package.

Provides tab lifecycle management, switching, grouping, and cross-tab
coordination for the autonomous browser agent.
"""

from tools.browser.tabs.models import TabEvent, TabEventRecord, TabGroup, TabInfo
from tools.browser.tabs.strategies import (
    ConservativeStrategy,
    ParallelStrategy,
    TabStrategy,
)
from tools.browser.tabs.coordinator import (
    MultiTabCoordinator,
    TabLimitExceeded,
    TabNotFoundError,
)

__all__ = [
    # Models
    "TabEvent",
    "TabEventRecord",
    "TabGroup",
    "TabInfo",
    # Strategies
    "TabStrategy",
    "ConservativeStrategy",
    "ParallelStrategy",
    # Coordinator
    "MultiTabCoordinator",
    "TabLimitExceeded",
    "TabNotFoundError",
]
