"""Observability models — Metrics, Tracing, and Health Check models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class HealthStatus(Enum):
    """Component health check state."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class PlatformMetric:
    """Prometheus-compatible metric sample."""

    name: str
    value: float
    metric_type: str = "counter"  # counter, gauge, histogram
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_prometheus_format(self) -> str:
        label_str = ",".join([f'{k}="{v}"' for k, v in self.labels.items()])
        if label_str:
            return f"{self.name}{{{label_str}}} {self.value}"
        return f"{self.name} {self.value}"


@dataclass
class TraceContext:
    """Distributed tracing context."""

    trace_id: str = field(default_factory=lambda: f"trc_{uuid.uuid4().hex[:12]}")
    span_id: str = field(default_factory=lambda: f"spn_{uuid.uuid4().hex[:8]}")
    parent_span_id: Optional[str] = None
    sampled: bool = True
