"""Processing Context Model flowing through pipeline steps."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time
from tools.document.config import DocumentConfig


@dataclass
class ProcessingContext:
    """Carries execution state, configuration, metrics, cancellation signals, and temporary pipeline artifacts."""

    config: DocumentConfig = field(default_factory=DocumentConfig)
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    cancelled: bool = False
    start_time: float = field(default_factory=time.time)
    metrics: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def record_metric(self, key: str, value: Any) -> None:
        """Record processing metric."""
        self.metrics[key] = value

    def add_warning(self, msg: str) -> None:
        """Add pipeline execution warning."""
        self.warnings.append(msg)

    def get_elapsed_seconds(self) -> float:
        """Get elapsed processing time in seconds."""
        return time.time() - self.start_time
