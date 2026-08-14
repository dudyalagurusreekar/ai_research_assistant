"""Clean Architecture Service for Workflows and Execution Tracking."""

from typing import List, Optional
from sqlalchemy.orm import Session

from infrastructure.database.models.workflow import ToolExecutionLog, Workflow, WorkflowExecution
from infrastructure.database.repositories.workflow_repository import WorkflowRepository


class WorkflowService:
    """Business logic service for Workflow Templates and Execution DAGs."""

    def __init__(self, db_session: Session):
        self.session = db_session
        self.repo = WorkflowRepository(db_session)

    def create_workflow(self, owner_id: str, name: str, dag_definition: dict) -> Workflow:
        """Create a workflow template."""
        return self.repo.create({
            "owner_id": owner_id,
            "name": name,
            "dag_definition": dag_definition,
            "is_active": True,
        })

    def list_workflows(self, owner_id: str) -> List[Workflow]:
        """List active workflows owned by user."""
        return self.session.query(Workflow).filter(Workflow.owner_id == owner_id, Workflow.is_active.is_(True)).all()

    def execute_workflow(self, workflow_id: str, input_params: dict) -> WorkflowExecution:
        """Start workflow execution run."""
        return self.repo.start_execution(workflow_id=workflow_id, input_params=input_params)

    def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Query workflow execution run state."""
        return self.session.query(WorkflowExecution).filter(WorkflowExecution.id == execution_id).first()
