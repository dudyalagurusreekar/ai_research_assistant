"""REST API Router for Workflows and Execution Tracking (/api/v1/workflows)."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.auth.dependencies import get_current_user, get_db_session
from infrastructure.database.models.auth import User
from services.api.schemas.envelope import ResponseEnvelope
from services.api.services.workflow_service import WorkflowService

router = APIRouter(prefix="", tags=["Workflows & Executions"])


class CreateWorkflowRequest(BaseModel):
    name: str
    dag_definition: dict


class ExecuteWorkflowRequest(BaseModel):
    input_params: Optional[dict] = None


@router.post("/workflows", status_code=status.HTTP_201_CREATED)
def create_workflow(
    req: CreateWorkflowRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Create a workflow template DAG."""
    service = WorkflowService(db)
    wf = service.create_workflow(owner_id=current_user.id, name=req.name, dag_definition=req.dag_definition)

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "id": wf.id,
            "owner_id": wf.owner_id,
            "name": wf.name,
            "dag_definition": wf.dag_definition,
        },
        correlation_id=correlation_id,
    )


@router.get("/workflows")
def list_workflows(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """List active workflows owned by current user."""
    service = WorkflowService(db)
    workflows = service.list_workflows(owner_id=current_user.id)

    correlation_id = getattr(request.state, "correlation_id", None)
    data = [{"id": w.id, "name": w.name, "dag_definition": w.dag_definition} for w in workflows]
    return ResponseEnvelope.success_response(data=data, correlation_id=correlation_id)


@router.post("/workflows/{workflow_id}/execute", status_code=status.HTTP_201_CREATED)
def execute_workflow(
    workflow_id: str,
    req: ExecuteWorkflowRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Trigger execution run for a workflow DAG."""
    service = WorkflowService(db)
    execution = service.execute_workflow(workflow_id, input_params=req.input_params or {})

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "execution_id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status,
            "started_at": execution.created_at.isoformat() if execution.created_at else None,
        },
        correlation_id=correlation_id,
    )


@router.get("/workflow-executions/{execution_id}")
def get_workflow_execution(
    execution_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Query status and node states of a workflow execution run."""
    service = WorkflowService(db)
    execution = service.get_execution_status(execution_id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Execution '{execution_id}' not found.")

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status,
            "input_params": execution.execution_data,
            "output_results": execution.execution_data,
        },
        correlation_id=correlation_id,
    )
