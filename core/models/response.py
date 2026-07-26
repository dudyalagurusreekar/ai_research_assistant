"""Response domain model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from core.models.artifact import Artifact
from core.utils.time_utils import utc_now


class ResponseStatus(Enum):
    """Status code for Response model."""

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    CANCELLED = "cancelled"


@dataclass
class Response:
    """Represents a structured platform response for a Request."""

    request_id: str
    session_id: str
    status: ResponseStatus
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    artifacts: List[Artifact] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Response to dictionary representation."""
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "artifacts": [art.to_dict() for art in self.artifacts],
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }
