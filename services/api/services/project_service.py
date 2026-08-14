"""Clean Architecture Service for Project & Workspace Domain Management."""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from infrastructure.database.models.project import Project, Workspace
from infrastructure.database.repositories.project_repository import ProjectRepository


class ProjectService:
    """Business logic service for Projects and Workspaces."""

    def __init__(self, db_session: Session):
        self.session = db_session
        self.repo = ProjectRepository(db_session)

    def create_project(self, owner_id: str, name: str, description: Optional[str] = None) -> Project:
        """Create a new project and default workspace."""
        project = self.repo.create({
            "name": name,
            "description": description,
            "owner_id": owner_id,
        })
        # Auto-create default workspace
        self.repo.create_workspace(project.id, name="Default Workspace", description="Default project workspace")
        return project

    def list_user_projects(self, user_id: str, skip: int = 0, limit: int = 20) -> Tuple[List[Project], int]:
        """List all projects owned by or accessible to user."""
        projects = self.repo.get_user_projects(user_id)
        total = len(projects)
        paginated = projects[skip : skip + limit]
        return paginated, total

    def get_project_by_id(self, project_id: str, user_id: str) -> Optional[Project]:
        """Retrieve project by ID verifying user ownership/access."""
        project = self.repo.get_by_id(project_id)
        if not project or project.owner_id != user_id:
            return None
        return project

    def update_project(self, project_id: str, user_id: str, name: Optional[str] = None, description: Optional[str] = None) -> Optional[Project]:
        """Update project details."""
        project = self.get_project_by_id(project_id, user_id)
        if not project:
            return None
        
        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description

        return self.repo.update(project_id, updates)

    def delete_project(self, project_id: str, user_id: str) -> bool:
        """Soft-delete project."""
        project = self.get_project_by_id(project_id, user_id)
        if not project:
            return False
        return self.repo.delete(project_id)

    def create_workspace(self, project_id: str, user_id: str, name: str, description: Optional[str] = None) -> Optional[Workspace]:
        """Create workspace under a project."""
        project = self.get_project_by_id(project_id, user_id)
        if not project:
            return None
        return self.repo.create_workspace(project_id, name=name, description=description)

    def list_workspaces(self, project_id: str, user_id: str) -> List[Workspace]:
        """List workspaces for a project."""
        project = self.get_project_by_id(project_id, user_id)
        if not project:
            return []
        return self.repo.get_project_workspaces(project_id)
