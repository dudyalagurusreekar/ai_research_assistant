"""ConnectorMetricsEngine for tracking latency, throughput, error rates, and Prometheus export."""

from dataclasses import dataclass, field
from typing import Dict, Any, List
import time
import json

from infrastructure.logging.logger import StructuredLogger


@dataclass
class ConnectorMetricsSnapshot:
    """Snapshot of telemetry metrics for a single connector."""
    connector_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limit_hits: int = 0
    total_latency_ms: float = 0.0
    tokens_consumed: int = 0
    last_error: str = ""
    last_request_timestamp: float = 0.0

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / max(1, self.total_requests)

    @property
    def error_rate_percent(self) -> float:
        return (self.failed_requests / max(1, self.total_requests)) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "connector_name": self.connector_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "rate_limit_hits": self.rate_limit_hits,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "error_rate_percent": round(self.error_rate_percent, 2),
            "tokens_consumed": self.tokens_consumed,
            "last_error": self.last_error,
        }


class ConnectorMetricsEngine:
    """Master metrics engine aggregating telemetry across connectors."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("ConnectorMetricsEngine")
        self._snapshots: Dict[str, ConnectorMetricsSnapshot] = {}

    def get_snapshot(self, connector_name: str) -> ConnectorMetricsSnapshot:
        """Retrieve or create snapshot for connector."""
        c = connector_name.lower()
        if c not in self._snapshots:
            self._snapshots[c] = ConnectorMetricsSnapshot(connector_name=c)
        return self._snapshots[c]

    def record_request(
        self,
        connector_name: str,
        success: bool,
        latency_ms: float,
        error_message: str = "",
        rate_limit_hit: bool = False,
        tokens_used: int = 0,
    ) -> None:
        """Record completed request telemetry."""
        snap = self.get_snapshot(connector_name)
        snap.total_requests += 1
        snap.total_latency_ms += latency_ms
        snap.last_request_timestamp = time.time()
        snap.tokens_consumed += tokens_used

        if success:
            snap.successful_requests += 1
        else:
            snap.failed_requests += 1
            snap.last_error = error_message

        if rate_limit_hit:
            snap.rate_limit_hits += 1

    def export_json(self) -> str:
        """Export all telemetry metrics in JSON format."""
        data = {k: v.to_dict() for k, v in self._snapshots.items()}
        return json.dumps(data, indent=2)

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus exposition format."""
        lines = []
        for name, snap in self._snapshots.items():
            lines.append(f'ara_connector_requests_total{{connector="{name}"}} {snap.total_requests}')
            lines.append(f'ara_connector_requests_success{{connector="{name}"}} {snap.successful_requests}')
            lines.append(f'ara_connector_requests_failed{{connector="{name}"}} {snap.failed_requests}')
            lines.append(f'ara_connector_latency_avg_ms{{connector="{name}"}} {snap.avg_latency_ms:.2f}')
            lines.append(f'ara_connector_tokens_consumed{{connector="{name}"}} {snap.tokens_consumed}')
        return "\n".join(lines)
