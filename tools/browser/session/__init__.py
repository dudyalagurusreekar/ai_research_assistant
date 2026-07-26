"""Session Orchestrator Package.

Provides top-level session lifecycle management for the autonomous browser agent,
including multi-goal coordination, persistence, and event hooks.
"""

from tools.browser.session.models import (
    GoalResult,
    SessionConfig,
    SessionMetadata,
    SessionState,
)
from tools.browser.session.hooks import (
    SessionHook,
    LoggingHook,
    MetricsHook,
)
from tools.browser.session.persistence import SessionPersistence
from tools.browser.session.orchestrator import SessionOrchestrator, SessionError

__all__ = [
    # Models
    "GoalResult",
    "SessionConfig",
    "SessionMetadata",
    "SessionState",
    # Hooks
    "SessionHook",
    "LoggingHook",
    "MetricsHook",
    # Persistence
    "SessionPersistence",
    # Orchestrator
    "SessionOrchestrator",
    "SessionError",
]
