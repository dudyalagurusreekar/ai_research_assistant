"""Communication models — Agent Messages and Routing."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class MessageType(Enum):
    """Structured message types for multi-agent communication."""

    DIRECT = "direct"
    BROADCAST = "broadcast"
    TASK_ASSIGNMENT = "task_assignment"
    RESULT = "result"
    ERROR = "error"
    REPLAN_REQUEST = "replan_request"
    FEEDBACK = "feedback"
    ARTIFACT_SHARE = "artifact_share"


class MessagePriority(Enum):
    """Priority levels for message handling."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentMessage:
    """Strongly typed message envelope for inter-agent communication."""

    sender_id: str
    recipient_id: Optional[str] = None  # None for BROADCAST
    message_type: MessageType = MessageType.DIRECT
    content: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    message_id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.value,
            "content": self.content,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
        }
