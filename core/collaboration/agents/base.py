"""Base Specialized Agent — Abstract foundation for all specialized AI agents."""

from __future__ import annotations

import abc
import uuid
from typing import Any, Dict, List, Optional

from core.collaboration.components.memory import CollaborationMemory
from core.collaboration.components.workspace import SharedWorkspace
from core.collaboration.models.agent_info import (
    AgentCapability,
    AgentMetadata,
    AgentRole,
    AgentStatus,
)
from core.collaboration.models.context import AgentOutput, TaskAssignment
from core.collaboration.models.message import AgentMessage, MessagePriority, MessageType
from utils.logger import get_logger

logger = get_logger("BaseSpecializedAgent")


class BaseSpecializedAgent(abc.ABC):
    """Abstract base class for all specialized agents in the collaboration framework."""

    def __init__(
        self,
        name: str,
        role: AgentRole,
        capabilities: Optional[List[AgentCapability]] = None,
        agent_id: Optional[str] = None,
    ) -> None:
        self.agent_id = agent_id or f"{role.value}_agent_{uuid.uuid4().hex[:6]}"
        self.name = name
        self.role = role
        self.capabilities = capabilities or []
        self.metadata = AgentMetadata(
            agent_id=self.agent_id,
            name=self.name,
            role=self.role,
            capabilities=self.capabilities,
            status=AgentStatus.IDLE,
        )

    def send_message(
        self,
        memory: CollaborationMemory,
        recipient_id: Optional[str],
        content: str,
        message_type: MessageType = MessageType.DIRECT,
        payload: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> AgentMessage:
        """Post a structured message into collaboration memory."""
        msg = AgentMessage(
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            message_type=message_type,
            content=content,
            payload=payload or {},
            priority=priority,
        )
        memory.post_message(msg)
        return msg

    def read_workspace(self, workspace: SharedWorkspace, key: str, default: Any = None) -> Any:
        """Convenience method to read from shared workspace."""
        return workspace.get(key, default=default)

    def write_workspace(
        self, workspace: SharedWorkspace, key: str, value: Any, artifact_type: str = "general"
    ) -> None:
        """Convenience method to write to shared workspace."""
        workspace.set(key, value, agent_id=self.agent_id, artifact_type=artifact_type)

    @abc.abstractmethod
    def execute_task(
        self,
        task: TaskAssignment,
        inputs: Dict[str, Any],
        workspace: SharedWorkspace,
        memory: CollaborationMemory,
    ) -> AgentOutput:
        """Execute a task assignment and return structured AgentOutput.

        Must be implemented by concrete specialized agent classes.
        """
        pass
