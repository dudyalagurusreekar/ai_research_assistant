"""Decision Response Package."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.decision_intelligence.models.recommendation import DecisionRecommendationReport


@dataclass
class DecisionResponse:
    """Output package from the Decision Intelligence Engine."""

    response_id: str = field(default_factory=lambda: f"dres_{uuid.uuid4().hex[:8]}")
    request_id: str = ""
    status: str = "success"  # success, partial, error
    report: Optional[DecisionRecommendationReport] = None
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response_id": self.response_id,
            "request_id": self.request_id,
            "status": self.status,
            "report": self.report.to_dict() if self.report else None,
            "execution_time_ms": self.execution_time_ms,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }
