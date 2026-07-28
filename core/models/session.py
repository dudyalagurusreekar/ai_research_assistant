"""Session domain model and state enum."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, unique
from typing import Any, Dict
from core.utils.id_generator import generate_id
from core.utils.time_utils import utc_now


@unique
class SessionState(Enum):
    """Lifecycle state of an execution session."""

    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


@dataclass
class Session:
    """Represents an execution session context in the platform."""

    user_id: str
    session_id: str = field(default_factory=lambda: generate_id("sess_"))
    state: SessionState = SessionState.CREATED
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_state(self, new_state: SessionState) -> None:
        """Update session lifecycle state and refresh updated_at timestamp."""
        self.state = new_state
        self.updated_at = utc_now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session to dictionary representation."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
