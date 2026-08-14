"""Metrics Engine for Sprint 11 Browser Automation Platform."""

import logging
import time
from typing import Any, Dict, Optional
from tools.browser.platform.models import ActionResult, BrowserMetrics

logger = logging.getLogger("Tools.Browser.Platform.MetricsEngine")


class BrowserMetricsEngine:
    """Tracks performance metrics, action counts, latency, security guardrail events, and CAPTCHA detections."""

    def __init__(self) -> None:
        self.metrics = BrowserMetrics()
        self._action_latencies: list[float] = []

    def record_action(self, result: ActionResult) -> None:
        """Record an action result into metrics tracker."""
        self.metrics.total_actions += 1
        if result.success:
            self.metrics.successful_actions += 1
        else:
            self.metrics.failed_actions += 1

        if result.action_type.value == "navigate":
            self.metrics.total_navigations += 1

        self.metrics.total_execution_time_ms += result.execution_time_ms
        self._action_latencies.append(result.execution_time_ms)
        self.metrics.average_action_latency_ms = sum(self._action_latencies) / len(self._action_latencies)

    def record_captcha_detected(self) -> None:
        """Record CAPTCHA detection event."""
        self.metrics.captchas_detected += 1

    def record_security_interception(self) -> None:
        """Record security guardrail block event."""
        self.metrics.security_interceptions += 1

    def set_active_contexts(self, count: int) -> None:
        """Update active context count."""
        self.metrics.active_contexts = count

    def get_summary(self) -> Dict[str, Any]:
        """Return exportable metrics dictionary summary."""
        success_rate = (
            (self.metrics.successful_actions / self.metrics.total_actions * 100)
            if self.metrics.total_actions > 0
            else 100.0
        )
        return {
            "total_actions": self.metrics.total_actions,
            "successful_actions": self.metrics.successful_actions,
            "failed_actions": self.metrics.failed_actions,
            "success_rate_pct": round(success_rate, 2),
            "total_navigations": self.metrics.total_navigations,
            "captchas_detected": self.metrics.captchas_detected,
            "security_interceptions": self.metrics.security_interceptions,
            "total_execution_time_ms": round(self.metrics.total_execution_time_ms, 2),
            "average_action_latency_ms": round(self.metrics.average_action_latency_ms, 2),
            "active_contexts": self.metrics.active_contexts,
        }

    def reset(self) -> None:
        """Reset all tracked metrics."""
        self.metrics = BrowserMetrics()
        self._action_latencies.clear()
