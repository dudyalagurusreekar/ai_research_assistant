"""Unit tests for structured message passing and collaboration memory."""

import pytest

from core.collaboration.components.memory import CollaborationMemory
from core.collaboration.models.message import AgentMessage, MessagePriority, MessageType


def test_post_and_receive_direct_message():
    memory = CollaborationMemory(session_id="test_session")
    msg = AgentMessage(
        sender_id="research_agent_1",
        recipient_id="writer_agent_1",
        message_type=MessageType.DIRECT,
        content="Research findings complete.",
        priority=MessagePriority.HIGH,
    )

    memory.post_message(msg)
    inbox = memory.get_inbox("writer_agent_1", clear_read=True)

    assert len(inbox) == 1
    assert inbox[0].content == "Research findings complete."
    assert inbox[0].sender_id == "research_agent_1"

    # Verify inbox cleared after reading
    second_fetch = memory.get_inbox("writer_agent_1")
    assert len(second_fetch) == 0


def test_broadcast_message():
    memory = CollaborationMemory(session_id="test_session")

    # Pre-register inboxes
    memory.get_inbox("agent_a")
    memory.get_inbox("agent_b")

    msg = AgentMessage(
        sender_id="orchestrator",
        recipient_id=None,  # Broadcast
        message_type=MessageType.BROADCAST,
        content="Global session started.",
    )
    memory.post_message(msg)

    inbox_a = memory.get_inbox("agent_a")
    inbox_b = memory.get_inbox("agent_b")

    assert len(inbox_a) == 1
    assert len(inbox_b) == 1
    assert inbox_a[0].content == "Global session started."


def test_message_priority_sorting():
    memory = CollaborationMemory(session_id="test_session")

    msg_low = AgentMessage(
        sender_id="agent_1", recipient_id="target", content="Low priority", priority=MessagePriority.LOW
    )
    msg_critical = AgentMessage(
        sender_id="agent_2", recipient_id="target", content="Critical priority", priority=MessagePriority.CRITICAL
    )
    msg_normal = AgentMessage(
        sender_id="agent_3", recipient_id="target", content="Normal priority", priority=MessagePriority.NORMAL
    )

    memory.post_message(msg_low)
    memory.post_message(msg_critical)
    memory.post_message(msg_normal)

    inbox = memory.get_inbox("target")
    assert len(inbox) == 3
    assert inbox[0].priority == MessagePriority.CRITICAL
    assert inbox[1].priority == MessagePriority.NORMAL
    assert inbox[2].priority == MessagePriority.LOW
