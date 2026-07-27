"""Browser Recovery package."""

from tools.browser.recovery.engine import BrowserRecoveryEngine

# Alias for backward compatibility across recovery tests
RecoveryEngine = BrowserRecoveryEngine

__all__ = [
    "BrowserRecoveryEngine",
    "RecoveryEngine",
]
