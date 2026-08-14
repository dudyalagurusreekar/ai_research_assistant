"""Research Sessions, Conversations, and Messages ORM models."""

from sqlalchemy import Column, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from infrastructure.database.models.base import BaseORMModel, Base, TimestampMixin, UUIDPrimaryKeyMixin


class ResearchSession(BaseORMModel):
    """Research session tracking goal, progress, and execution state."""

    __tablename__ = "research_sessions"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    goal = Column(Text, nullable=False)
    status = Column(String(50), default="active", nullable=False, index=True)  # active, completed, failed, archived
    context_data = Column(JSON, default=dict, nullable=False)

    user = relationship("User", back_populates="research_sessions")
    project = relationship("Project", back_populates="research_sessions")
    conversations = relationship("Conversation", back_populates="research_session", cascade="all, delete-orphan")
    workflows = relationship("WorkflowExecution", back_populates="research_session", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="research_session", cascade="all, delete-orphan")


class Conversation(BaseORMModel):
    """Conversation thread belonging to a research session."""

    __tablename__ = "conversations"

    session_id = Column(String(36), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    model_name = Column(String(100), default="gemini-2.5-pro", nullable=False)
    system_prompt = Column(Text, nullable=True)

    research_session = relationship("ResearchSession", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Individual chat/tool message within a conversation."""

    __tablename__ = "messages"

    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(50), nullable=False, index=True)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    extra_metadata = Column(JSON, default=dict, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")
    attachments = relationship("MessageAttachment", back_populates="message", cascade="all, delete-orphan")


class MessageAttachment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """File attachment linked to a message."""

    __tablename__ = "message_attachments"

    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_path = Column(String(512), nullable=False)
    minio_bucket = Column(String(100), nullable=False)

    message = relationship("Message", back_populates="attachments")
