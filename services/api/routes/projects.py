"""REST API Router for Project and Workspace Management (/api/v1/projects)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.auth.dependencies import get_current_user, get_db_session
from infrastructure.database.models.auth import User
from services.api.schemas.envelope import PaginationMeta, ResponseEnvelope
from services.api.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects & Workspaces"])


class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CreateWorkspaceRequest(BaseModel):
    name: str
    description: Optional[str] = None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_project(
    req: CreateProjectRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Create a new research project with a default workspace."""
    service = ProjectService(db)
    project = service.create_project(owner_id=current_user.id, name=req.name, description=req.description)
    
    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "owner_id": project.owner_id,
            "created_at": project.created_at.isoformat() if project.created_at else None,
        },
        correlation_id=correlation_id,
    )


@router.get("")
def list_projects(
    page: int = 1,
    limit: int = 20,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """List projects accessible to the current authenticated user."""
    service = ProjectService(db)
    skip = (page - 1) * limit
    projects, total = service.list_user_projects(current_user.id, skip=skip, limit=limit)
    
    meta = PaginationMeta(
        page=page,
        limit=limit,
        total_items=total,
        total_pages=(total + limit - 1) // limit if limit > 0 else 1,
    )
    correlation_id = getattr(request.state, "correlation_id", None) if request else None
    
    data = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "owner_id": p.owner_id,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in projects
    ]
    return ResponseEnvelope.success_response(data=data, meta=meta, correlation_id=correlation_id)


@router.get("/{project_id}")
def get_project(
    project_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Get project details by ID."""
    service = ProjectService(db)
    project = service.get_project_by_id(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found.")

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "owner_id": project.owner_id,
            "created_at": project.created_at.isoformat() if project.created_at else None,
        },
        correlation_id=correlation_id,
    )


@router.patch("/{project_id}")
def update_project(
    project_id: str,
    req: UpdateProjectRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Update project details."""
    service = ProjectService(db)
    project = service.update_project(project_id, current_user.id, name=req.name, description=req.description)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found.")

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "id": project.id,
            "name": project.name,
            "description": project.description,
        },
        correlation_id=correlation_id,
    )


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Soft-delete project."""
    service = ProjectService(db)
    success = service.delete_project(project_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found.")

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={"message": f"Project '{project_id}' deleted successfully."},
        correlation_id=correlation_id,
    )


@router.post("/{project_id}/workspaces", status_code=status.HTTP_201_CREATED)
def create_workspace(
    project_id: str,
    req: CreateWorkspaceRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Create workspace under project."""
    service = ProjectService(db)
    ws = service.create_workspace(project_id, current_user.id, name=req.name, description=req.description)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found.")

    correlation_id = getattr(request.state, "correlation_id", None)
    return ResponseEnvelope.success_response(
        data={
            "id": ws.id,
            "project_id": ws.project_id,
            "name": ws.name,
            "description": ws.description,
        },
        correlation_id=correlation_id,
    )


@router.get("/{project_id}/workspaces")
def list_workspaces(
    project_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """List workspaces under a project."""
    service = ProjectService(db)
    workspaces = service.list_workspaces(project_id, current_user.id)
    
    correlation_id = getattr(request.state, "correlation_id", None)
    data = [{"id": w.id, "project_id": w.project_id, "name": w.name, "description": w.description} for w in workspaces]
    return ResponseEnvelope.success_response(data=data, correlation_id=correlation_id)
