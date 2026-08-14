"""Workflow Execution and Tool Log Repository implementation."""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from infrastructure.database.models.workflow import ToolExecutionLog, Workflow, WorkflowExecution, WorkflowNodeState
from infrastructure.database.repositories.base import BaseRepository


class WorkflowRepository(BaseRepository[Workflow]):
    """Repository for managing workflow DAG templates and tool logs."""

    def __init__(self, session: Session):
        super().__init__(Workflow, session)

    def start_execution(self, workflow_id: str, input_params: dict, research_session_id: Optional[str] = None) -> WorkflowExecution:
        """Start workflow execution run."""
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            research_session_id=research_session_id or "00000000-0000-0000-0000-000000000000",
            status="running",
            execution_data=input_params,
        )
        self.session.add(execution)
        self.session.flush()
        return execution

    def log_tool_execution(
        self,
        tool_name: str,
        input_params: Dict[str, Any],
        output_result: Dict[str, Any],
        duration_ms: float,
        status: str = "success",
        workflow_execution_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> ToolExecutionLog:
        """Log a tool execution event for observability and audit."""
        tool_log = ToolExecutionLog(
            workflow_execution_id=workflow_execution_id,
            tool_name=tool_name,
            input_params=input_params,
            output_result=output_result,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
        )
        self.session.add(tool_log)
        self.session.flush()
        return tool_log

    def set_node_state(
        self,
        workflow_execution_id: str,
        node_id: str,
        status: str,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        latency_ms: float = 0.0,
    ) -> WorkflowNodeState:
        """Record or update execution state for a DAG node."""
        node_state = (
            self.session.query(WorkflowNodeState)
            .filter(
                WorkflowNodeState.workflow_execution_id == workflow_execution_id,
                WorkflowNodeState.node_id == node_id,
            )
            .first()
        )

        if not node_state:
            node_state = WorkflowNodeState(
                workflow_execution_id=workflow_execution_id,
                node_id=node_id,
                status=status,
                input_data=input_data or {},
                output_data=output_data or {},
                latency_ms=latency_ms,
            )
            self.session.add(node_state)
        else:
            node_state.status = status
            if input_data:
                node_state.input_data = input_data
            if output_data:
                node_state.output_data = output_data
            node_state.latency_ms = latency_ms

        self.session.flush()
        return node_state
