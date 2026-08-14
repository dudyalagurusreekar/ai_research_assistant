"""Workflows, Node States, and Tool Execution Logs ORM models."""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from infrastructure.database.models.base import BaseORMModel, Base, TimestampMixin, UUIDPrimaryKeyMixin


class Workflow(BaseORMModel):
    """Workflow DAG template definition."""

    __tablename__ = "workflows"

    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    dag_definition = Column(JSON, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowExecution(BaseORMModel):
    """Execution run instance of a workflow DAG."""

    __tablename__ = "workflow_executions"

    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True, index=True)
    research_session_id = Column(String(36), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=True, index=True)
    status = Column(String(50), default="running", nullable=False, index=True)  # pending, running, completed, failed
    completed_steps = Column(Integer, default=0, nullable=False)
    total_steps = Column(Integer, default=0, nullable=False)
    execution_data = Column(JSON, default=dict, nullable=False)

    workflow = relationship("Workflow", back_populates="executions")
    research_session = relationship("ResearchSession", back_populates="workflows")
    node_states = relationship("WorkflowNodeState", back_populates="workflow_execution", cascade="all, delete-orphan")
    tool_logs = relationship("ToolExecutionLog", back_populates="workflow_execution", cascade="all, delete-orphan")


class WorkflowNodeState(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """State tracking for an individual node in a workflow DAG."""

    __tablename__ = "workflow_node_states"

    workflow_execution_id = Column(String(36), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    node_id = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, running, success, failed, skipped
    input_data = Column(JSON, default=dict, nullable=False)
    output_data = Column(JSON, default=dict, nullable=False)
    latency_ms = Column(Float, default=0.0, nullable=False)

    workflow_execution = relationship("WorkflowExecution", back_populates="node_states")


class ToolExecutionLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Execution metrics and trace log for tools invoked by agents."""

    __tablename__ = "tool_execution_logs"

    workflow_execution_id = Column(String(36), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=True, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    input_params = Column(JSON, default=dict, nullable=False)
    output_result = Column(JSON, default=dict, nullable=False)
    duration_ms = Column(Float, nullable=False)
    status = Column(String(50), default="success", nullable=False, index=True)  # success, error, timeout
    error_message = Column(Text, nullable=True)

    workflow_execution = relationship("WorkflowExecution", back_populates="tool_logs")
