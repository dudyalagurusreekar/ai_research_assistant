"""Request domain model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict
from core.utils.id_generator import generate_id
from core.utils.time_utils import utc_now


@dataclass
class Request:
    """Represents a unified user or system request passed through the platform."""

    intent: str
    session_id: str
    request_id: str = field(default_factory=lambda: generate_id("req_"))
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize request to dictionary representation."""
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "intent": self.intent,
            "parameters": self.parameters,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }
