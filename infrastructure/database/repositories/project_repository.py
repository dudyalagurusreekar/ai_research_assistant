"""Project and Workspace Repository implementation."""

from typing import List, Optional
from sqlalchemy.orm import Session
from infrastructure.database.models.project import Project, ProjectMember, Workspace
from infrastructure.database.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for managing projects and project workspaces."""

    def __init__(self, session: Session):
        super().__init__(Project, session)

    def get_user_projects(self, user_id: str) -> List[Project]:
        """Fetch all projects owned by or shared with a user."""
        return (
            self.session.query(Project)
            .outerjoin(ProjectMember, ProjectMember.project_id == Project.id)
            .filter((Project.owner_id == user_id) | (ProjectMember.user_id == user_id))
            .filter(Project.is_deleted.is_(False))
            .distinct()
            .all()
        )


    def add_member(self, project_id: str, user_id: str, role: str = "collaborator") -> ProjectMember:
        """Add a user member to a project."""
        member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
        self.session.add(member)
        self.session.flush()
        return member

    def create_workspace(self, project_id: str, name: str, description: Optional[str] = None) -> Workspace:
        """Create a workspace under a project."""
        workspace = Workspace(project_id=project_id, name=name, description=description)
        self.session.add(workspace)
        self.session.flush()
        return workspace

    def get_project_workspaces(self, project_id: str) -> List[Workspace]:
        """List all workspaces in a project."""
        return (
            self.session.query(Workspace)
            .filter(Workspace.project_id == project_id, Workspace.is_deleted.is_(False))
            .all()
        )
