"""Project, Workspace, and Collaboration ORM models."""

from sqlalchemy import Column, ForeignKey, String, Text, JSON
from sqlalchemy.orm import relationship
from infrastructure.database.models.base import BaseORMModel, Base, TimestampMixin, UUIDPrimaryKeyMixin


class Project(BaseORMModel):
    """Project organizational unit model."""

    __tablename__ = "projects"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=True, index=True)
    visibility = Column(String(50), default="private", nullable=False)
    settings = Column(JSON, default=dict, nullable=False)

    # Relationships
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    workspaces = relationship("Workspace", back_populates="project", cascade="all, delete-orphan")
    research_sessions = relationship("ResearchSession", back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Project membership and role assignment."""

    __tablename__ = "project_members"

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), default="collaborator", nullable=False)  # owner, admin, collaborator, viewer

    project = relationship("Project", back_populates="members")
    user = relationship("User")


class Workspace(BaseORMModel):
    """Workspace container within a project for managing datasets and sessions."""

    __tablename__ = "workspaces"

    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    settings = Column(JSON, default=dict, nullable=False)

    project = relationship("Project", back_populates="workspaces")
    documents = relationship("Document", back_populates="workspace", cascade="all, delete-orphan")
