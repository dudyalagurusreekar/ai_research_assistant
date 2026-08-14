"""Unit test for ObservabilityManager."""

import pytest

from core.platform_infra.components.observability_manager import ObservabilityManager


def test_observability_metrics_and_health():
    obs = ObservabilityManager()

    obs.record_counter("requests_total", 1.0, {"path": "/healthz"})
    obs.record_gauge("active_users", 42.0)

    prom_text = obs.export_prometheus_metrics()
    assert "requests_total" in prom_text
    assert "active_users" in prom_text

    liveness = obs.get_liveness()
    readiness = obs.get_readiness()

    assert liveness["status"] == "healthy"
    assert readiness["status"] == "ready"
