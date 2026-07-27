"""Distributed Tracing, Timeline, Execution Snapshots, and Diagnostics."""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from core.utils.id_generator import generate_id
from core.utils.time_utils import utc_isoformat


@dataclass
class TraceSpan:
    """Represents a single span in a distributed trace."""

    span_id: str = field(default_factory=lambda: generate_id("span_"))
    name: str = ""
    trace_id: str = ""
    parent_span_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    status: str = "OK"
    attributes: Dict[str, Any] = field(default_factory=dict)

    def finish(self, status: str = "OK") -> None:
        """Mark span as finished and compute duration."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000.0
        self.status = status


class ObservabilityTracer:
    """Provides distributed tracing, event timeline recording, execution snapshots, and diagnostic reports."""

    def __init__(self, trace_id: Optional[str] = None) -> None:
        self.trace_id = trace_id or generate_id("trace_")
        self.spans: List[TraceSpan] = []
        self.timeline: List[Dict[str, Any]] = []
        self.snapshots: List[Dict[str, Any]] = []

    def start_span(self, name: str, parent_span_id: Optional[str] = None) -> TraceSpan:
        """Start a new trace span."""
        span = TraceSpan(name=name, trace_id=self.trace_id, parent_span_id=parent_span_id)
        self.spans.append(span)
        self.record_event(f"span_start.{name}", {"span_id": span.span_id})
        return span

    def record_event(self, event_name: str, payload: Optional[Dict[str, Any]] = None) -> None:
        """Add an entry to the event timeline."""
        self.timeline.append({
            "timestamp": utc_isoformat(),
            "event": event_name,
            "payload": payload or {},
        })

    def capture_snapshot(self, label: str, state_dict: Dict[str, Any]) -> None:
        """Capture an execution state snapshot."""
        self.snapshots.append({
            "snapshot_id": generate_id("snap_"),
            "label": label,
            "timestamp": utc_isoformat(),
            "state": state_dict,
        })

    def generate_diagnostic_report(self) -> Dict[str, Any]:
        """Compile a complete diagnostic report."""
        finished_spans = [
            {
                "span_id": s.span_id,
                "name": s.name,
                "duration_ms": round(s.duration_ms, 2),
                "status": s.status,
                "attributes": s.attributes,
            }
            for s in self.spans
        ]
        return {
            "trace_id": self.trace_id,
            "total_spans": len(self.spans),
            "spans": finished_spans,
            "timeline_length": len(self.timeline),
            "timeline": self.timeline,
            "snapshot_count": len(self.snapshots),
            "snapshots": self.snapshots,
        }
