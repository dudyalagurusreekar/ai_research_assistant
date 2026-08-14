"""Collaboration Memory — Thread-safe inter-agent message buffer and dialog history."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from core.collaboration.models.message import AgentMessage, MessagePriority, MessageType
from utils.logger import get_logger

logger = get_logger("CollaborationMemory")


class CollaborationMemory:
    """Thread-safe memory store for inter-agent messages and structured dialog history."""

    def __init__(self, session_id: str = "global_session") -> None:
        self.session_id = session_id
        self._messages: List[AgentMessage] = []
        self._recipient_inbox: Dict[str, List[AgentMessage]] = {}
        self._lock = threading.RLock()

    def post_message(self, message: AgentMessage) -> AgentMessage:
        """Post a message into memory and deliver to target recipient's inbox or broadcast."""
        with self._lock:
            self._messages.append(message)

            if message.recipient_id:
                if message.recipient_id not in self._recipient_inbox:
                    self._recipient_inbox[message.recipient_id] = []
                self._recipient_inbox[message.recipient_id].append(message)
            else:
                # Broadcast message: deliver to all known inboxes
                for inbox in self._recipient_inbox.values():
                    inbox.append(message)

            logger.debug(
                f"Memory [{self.session_id}] Message {message.message_id} posted by '{message.sender_id}' "
                f"to '{message.recipient_id or 'BROADCAST'}' [{message.message_type.value}]"
            )
            return message

    def get_inbox(self, agent_id: str, clear_read: bool = False) -> List[AgentMessage]:
        """Fetch unread messages for a specific agent inbox."""
        with self._lock:
            if agent_id not in self._recipient_inbox:
                self._recipient_inbox[agent_id] = []
            messages = list(self._recipient_inbox[agent_id])
            if clear_read:
                self._recipient_inbox[agent_id] = []
            return sorted(messages, key=lambda m: m.priority.value, reverse=True)

    def get_conversation_history(
        self,
        sender_id: Optional[str] = None,
        recipient_id: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        limit: int = 100,
    ) -> List[AgentMessage]:
        """Query conversation history filtered by sender, recipient, or message type."""
        with self._lock:
            filtered = []
            for msg in self._messages:
                if sender_id and msg.sender_id != sender_id:
                    continue
                if recipient_id and msg.recipient_id != recipient_id:
                    continue
                if message_type and msg.message_type != message_type:
                    continue
                filtered.append(msg)
            return filtered[-limit:]

    def get_all_messages(self) -> List[AgentMessage]:
        """Retrieve complete message stream."""
        with self._lock:
            return list(self._messages)

    def clear(self) -> None:
        """Clear memory buffer."""
        with self._lock:
            self._messages.clear()
            self._recipient_inbox.clear()
            logger.debug(f"Memory [{self.session_id}] cleared.")
