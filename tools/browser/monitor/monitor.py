"""Runtime Telemetry, Event Monitoring & Loop Detection (`tools/browser/monitor/monitor.py`).

Observes BrowserState events via an EventDispatcher, tracking latency, token usage,
navigation cycles, and potential execution loops without polling.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from tools.browser.browser.events import (
    BrowserEvent,
    BrowserEventType,
    EventDispatcher,
)

logger = logging.getLogger("BrowserMonitor")


@dataclass
class TelemetryStats:
    """Aggregated runtime statistics for an agent execution session."""

    events_received: int = 0
    url_changes: int = 0
    dom_changes: int = 0
    rollbacks: int = 0
    loops_detected: int = 0
    total_duration_ms: float = 0.0
    total_tokens_used: int = 0
    average_prompt_size: float = 0.0
    cache_hit_rate: float = 0.0
    average_planning_latency_ms: float = 0.0
    browser_action_latency_ms: float = 0.0
    verification_latency_ms: float = 0.0
    provider_failover_count: int = 0


class BrowserMonitor:
    """Event-driven runtime monitor for BrowserState and agent execution.

    Subscribes to an EventDispatcher to observe state transitions, detect action
    loops, and track execution budget and telemetry.
    """

    def __init__(
        self,
        dispatcher: Optional[EventDispatcher] = None,
        max_loop_threshold: int = 3,
    ) -> None:
        """Initialize BrowserMonitor.

        Args:
            dispatcher (Optional[EventDispatcher]): Target EventDispatcher to subscribe to.
            max_loop_threshold (int): Max consecutive identical URLs/actions before loop alert.
        """
        self.dispatcher = dispatcher
        self.max_loop_threshold = max_loop_threshold
        self.stats = TelemetryStats()
        self.url_history: List[str] = []
        self.recent_actions: List[str] = []
        self._prompt_count: int = 0
        self._cache_hits: int = 0
        self._planning_count: int = 0
        self._total_planning_ms: float = 0.0
        self._action_count: int = 0
        self._total_action_ms: float = 0.0
        self._verification_count: int = 0
        self._total_verification_ms: float = 0.0
        self._logger = logger

        if self.dispatcher:
            self.dispatcher.subscribe(self.on_event)

    def attach(self, dispatcher: EventDispatcher) -> None:
        """Attach monitor to a new EventDispatcher."""
        if self.dispatcher:
            self.dispatcher.unsubscribe(self.on_event)
        self.dispatcher = dispatcher
        self.dispatcher.subscribe(self.on_event)

    def on_event(self, event: BrowserEvent) -> None:
        """Handle incoming browser events."""
        self.stats.events_received += 1

        if event.event_type == BrowserEventType.URL_CHANGED:
            self.stats.url_changes += 1
            new_url = str(event.new_value) if event.new_value else ""
            self._record_url(new_url)

        elif event.event_type == BrowserEventType.DOM_CHANGED:
            self.stats.dom_changes += 1

        elif event.event_type == BrowserEventType.STATE_ROLLED_BACK:
            self.stats.rollbacks += 1
            self._logger.warning(
                f"State rollback detected: version {event.old_value} -> {event.new_value}"
            )

    def _record_url(self, url: str) -> None:
        """Record URL and check for navigation loops."""
        if not url:
            return
        self.url_history.append(url)
        if len(self.url_history) >= self.max_loop_threshold:
            recent = self.url_history[-self.max_loop_threshold :]
            if len(set(recent)) == 1:
                self.stats.loops_detected += 1
                self._logger.warning(
                    f"Navigation loop detected: URL '{url}' visited {self.max_loop_threshold} times consecutively."
                )

    def check_action_loop(self, action_signature: str) -> bool:
        """Check if an action signature is repeating in a loop.

        Args:
            action_signature (str): Signature representing action and selector/url.

        Returns:
            bool: True if loop detected.
        """
        self.recent_actions.append(action_signature)
        if len(self.recent_actions) >= self.max_loop_threshold:
            recent = self.recent_actions[-self.max_loop_threshold :]
            if len(set(recent)) == 1:
                self.stats.loops_detected += 1
                self._logger.warning(f"Action loop detected: '{action_signature}' repeated.")
                return True
        return False

    def record_prompt_tokens(self, tokens: int, cached: bool = False) -> None:
        """Record token usage and update prompt size and cache hit rate metrics."""
        self._prompt_count += 1
        self.stats.total_tokens_used += tokens
        self.stats.average_prompt_size = self.stats.total_tokens_used / max(1, self._prompt_count)
        if cached:
            self._cache_hits += 1
        self.stats.cache_hit_rate = (self._cache_hits / max(1, self._prompt_count)) * 100.0

    def record_planning_latency(self, duration_ms: float) -> None:
        """Record LLM/planning duration."""
        self._planning_count += 1
        self._total_planning_ms += duration_ms
        self.stats.average_planning_latency_ms = self._total_planning_ms / max(1, self._planning_count)

    def record_action_latency(self, duration_ms: float) -> None:
        """Record browser action duration."""
        self._action_count += 1
        self._total_action_ms += duration_ms
        self.stats.browser_action_latency_ms = self._total_action_ms / max(1, self._action_count)

    def record_verification_latency(self, duration_ms: float) -> None:
        """Record action verification duration."""
        self._verification_count += 1
        self._total_verification_ms += duration_ms
        self.stats.verification_latency_ms = self._total_verification_ms / max(1, self._verification_count)

    def record_failover(self) -> None:
        """Increment model provider failover count."""
        self.stats.provider_failover_count += 1

    def get_stats_dict(self) -> Dict[str, Any]:
        """Return serialized telemetry stats."""
        return {
            "events_received": self.stats.events_received,
            "url_changes": self.stats.url_changes,
            "dom_changes": self.stats.dom_changes,
            "rollbacks": self.stats.rollbacks,
            "loops_detected": self.stats.loops_detected,
            "total_tokens_used": self.stats.total_tokens_used,
            "average_prompt_size": round(self.stats.average_prompt_size, 2),
            "cache_hit_rate": round(self.stats.cache_hit_rate, 2),
            "average_planning_latency_ms": round(self.stats.average_planning_latency_ms, 2),
            "browser_action_latency_ms": round(self.stats.browser_action_latency_ms, 2),
            "verification_latency_ms": round(self.stats.verification_latency_ms, 2),
            "provider_failover_count": self.stats.provider_failover_count,
        }
