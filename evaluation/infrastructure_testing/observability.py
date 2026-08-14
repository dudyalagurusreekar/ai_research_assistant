"""Observability and Telemetry Platform — Prometheus metric exporters, Grafana dashboard specifications, and OpenTelemetry instrumentation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from utils.logger import get_logger

logger = get_logger("ObservabilityPlatform")


class PrometheusMetricExporter:
    """Exports structured metrics in Prometheus text format (# HELP, # TYPE, gauges, counters)."""

    def __init__(self) -> None:
        self._gauges: Dict[str, Tuple[float, str]] = {}
        self._counters: Dict[str, Tuple[float, str]] = {}

    def set_gauge(self, name: str, value: float, help_text: str = "") -> None:
        self._gauges[name] = (value, help_text)

    def inc_counter(self, name: str, value: float = 1.0, help_text: str = "") -> None:
        curr, h = self._counters.get(name, (0.0, help_text))
        self._counters[name] = (curr + value, help_text or h)

    def generate_prometheus_text(self) -> str:
        """Generate Prometheus exposition format string."""
        lines = []

        for name, (val, help_text) in self._counters.items():
            if help_text:
                lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {val:.4f}")

        for name, (val, help_text) in self._gauges.items():
            if help_text:
                lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {val:.4f}")

        return "\n".join(lines) + "\n"


class GrafanaDashboardGenerator:
    """Generates structured Grafana Dashboard JSON specifications for ARA evaluation & telemetry monitoring."""

    def __init__(self, title: str = "ARA v1.0 Production Evaluation & Telemetry Dashboard") -> None:
        self.title = title

    def generate_dashboard_json(self, metrics_summary: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a complete Grafana dashboard specification dictionary."""
        metrics_summary = metrics_summary or {}
        return {
            "dashboard": {
                "id": None,
                "title": self.title,
                "tags": ["ara", "evaluation", "telemetry", "observability"],
                "timezone": "browser",
                "schemaVersion": 16,
                "version": 1,
                "refresh": "10s",
                "panels": [
                    {
                        "id": 1,
                        "title": "Overall Quality Score",
                        "type": "stat",
                        "targets": [{"expr": "ara_evaluation_quality_score"}],
                        "gridPos": {"x": 0, "y": 0, "w": 6, "h": 4},
                    },
                    {
                        "id": 2,
                        "title": "Overall Pass Rate (%)",
                        "type": "stat",
                        "targets": [{"expr": "ara_evaluation_pass_rate"}],
                        "gridPos": {"x": 6, "y": 0, "w": 6, "h": 4},
                    },
                    {
                        "id": 3,
                        "title": "Average Execution Latency (ms)",
                        "type": "graph",
                        "targets": [{"expr": "ara_evaluation_latency_ms"}],
                        "gridPos": {"x": 12, "y": 0, "w": 12, "h": 4},
                    },
                    {
                        "id": 4,
                        "title": "Hallucination Rate & Groundedness",
                        "type": "graph",
                        "targets": [
                            {"expr": "ara_evaluation_hallucination_rate"},
                            {"expr": "ara_evaluation_groundedness_score"},
                        ],
                        "gridPos": {"x": 0, "y": 4, "w": 12, "h": 6},
                    },
                    {
                        "id": 5,
                        "title": "Category Pass Rates",
                        "type": "bargauge",
                        "targets": [{"expr": "ara_evaluation_category_pass_rate"}],
                        "gridPos": {"x": 12, "y": 4, "w": 12, "h": 6},
                    },
                ],
            },
            "overwrite": True,
        }


class OpenTelemetrySpanTracer:
    """Instrumentation tracer recording evaluation execution spans and attributes."""

    def __init__(self) -> None:
        self.spans: List[Dict[str, Any]] = []

    def start_span(self, span_name: str, attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Record span start."""
        span = {
            "span_name": span_name,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {},
            "events": [],
            "status": "OK",
        }
        self.spans.append(span)
        logger.debug(f"OpenTelemetrySpanTracer started span '{span_name}'")
        return span

    def end_span(self, span: Dict[str, Any], status: str = "OK", end_attributes: Optional[Dict[str, Any]] = None) -> None:
        """Record span completion."""
        span["end_time"] = datetime.now(timezone.utc).isoformat()
        span["status"] = status
        if end_attributes:
            span["attributes"].update(end_attributes)
        logger.debug(f"OpenTelemetrySpanTracer ended span '{span['span_name']}' with status '{status}'")
