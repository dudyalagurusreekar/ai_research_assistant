"""Event domain model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict
from core.utils.id_generator import generate_id
from core.utils.time_utils import utc_now


@dataclass
class Event:
    """Represents a domain event published across the platform event bus."""

    event_type: str
    source: str
    payload: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: generate_id("evt_"))
    timestamp: datetime = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary representation."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
        }
