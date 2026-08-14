"""Observability Manager — Prometheus metrics collection, distributed trace propagation, and health check endpoints."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from core.platform_infra.models.observability import HealthStatus, PlatformMetric, TraceContext
from utils.logger import get_logger

logger = get_logger("ObservabilityManager")


class ObservabilityManager:
    """Manages system metrics, distributed tracing, and health check endpoints."""

    def __init__(self) -> None:
        self._metrics: Dict[str, PlatformMetric] = {}
        self._component_health: Dict[str, HealthStatus] = {}

        # Default system health statuses
        self.set_component_health("planner", HealthStatus.HEALTHY)
        self.set_component_health("collaboration", HealthStatus.HEALTHY)
        self.set_component_health("knowledge_graph", HealthStatus.HEALTHY)
        self.set_component_health("workflow", HealthStatus.HEALTHY)

    def record_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Record or increment counter metric."""
        labels = labels or {}
        key = f"{name}_{sorted(labels.items())}"

        if key in self._metrics:
            self._metrics[key].value += value
        else:
            self._metrics[key] = PlatformMetric(name=name, value=value, metric_type="counter", labels=labels)

    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record gauge metric."""
        labels = labels or {}
        key = f"{name}_{sorted(labels.items())}"
        self._metrics[key] = PlatformMetric(name=name, value=value, metric_type="gauge", labels=labels)

    def export_prometheus_metrics(self) -> str:
        """Export metrics in standard Prometheus text format."""
        lines = [m.to_prometheus_format() for m in self._metrics.values()]
        return "\n".join(lines)

    def create_trace(self, parent_trace_id: Optional[str] = None) -> TraceContext:
        """Create new trace context or extend existing trace ID."""
        if parent_trace_id:
            return TraceContext(trace_id=parent_trace_id)
        return TraceContext()

    def set_component_health(self, component_name: str, status: HealthStatus) -> None:
        """Update component health status."""
        self._component_health[component_name] = status

    def get_liveness(self) -> Dict[str, Any]:
        """Liveness check endpoint logic (`/healthz`)."""
        return {"status": "healthy", "uptime_seconds": time.time()}

    def get_readiness(self) -> Dict[str, Any]:
        """Readiness check endpoint logic (`/readyz`)."""
        is_ready = all(s != HealthStatus.UNHEALTHY for s in self._component_health.values())
        return {
            "status": "ready" if is_ready else "not_ready",
            "components": {k: v.value for k, v in self._component_health.items()},
        }
