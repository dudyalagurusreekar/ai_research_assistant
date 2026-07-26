"""Monitor Layer (`tools/browser/monitor/`).

Provides Event-Driven runtime monitoring, loop detection, and telemetry tracking
for browser state and agent execution without polling.
"""

from tools.browser.monitor.monitor import (
    BrowserMonitor,
    TelemetryStats,
)

__all__ = [
    "BrowserMonitor",
    "TelemetryStats",
]
