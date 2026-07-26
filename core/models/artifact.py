"""Artifact domain model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from core.utils.id_generator import generate_id
from core.utils.time_utils import utc_now


@dataclass
class Artifact:
    """Represents an artifact generated or consumed during execution."""

    name: str
    artifact_type: str
    artifact_id: str = field(default_factory=lambda: generate_id("art_"))
    uri_or_path: Optional[str] = None
    content: Optional[Any] = None
    mime_type: str = "text/plain"
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize artifact to dictionary representation."""
        return {
            "artifact_id": self.artifact_id,
            "name": self.name,
            "artifact_type": self.artifact_type,
            "uri_or_path": self.uri_or_path,
            "mime_type": self.mime_type,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }
