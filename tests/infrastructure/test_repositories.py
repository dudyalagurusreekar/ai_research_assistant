import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from infrastructure.database.connection import DatabaseManager
from infrastructure.database.models import Base, User
from infrastructure.database.repositories import (
    AuditLogRepository,
    ProjectRepository,
    ResearchSessionRepository,
    UserRepository,
    WorkflowRepository,
)


@pytest.fixture
def db_session():
    manager = DatabaseManager("sqlite:///:memory:")
    manager.create_all_tables(Base)
    with manager.get_session() as session:
        yield session
    manager.drop_all_tables(Base)


def test_user_repository_crud_and_email(db_session):
    repo = UserRepository(db_session)
    user = repo.create({
        "email": "repo_user@ara.local",
        "full_name": "Repo User",
        "password_hash": "hash123",
    })
    assert user.id is not None
    assert user.email == "repo_user@ara.local"

    found = repo.get_by_email("repo_user@ara.local")
    assert found is not None
    assert found.id == user.id

    # Test list and pagination
    users = repo.list(skip=0, limit=10)
    assert len(users) == 1

    # Test update
    updated = repo.update(user.id, {"full_name": "Updated Repo User"})
    assert updated.full_name == "Updated Repo User"

    # Test soft delete
    deleted = repo.delete(user.id, hard_delete=False)
    assert deleted is True
    assert repo.get_by_email("repo_user@ara.local") is None


def test_project_repository(db_session):
    user_repo = UserRepository(db_session)
    user = user_repo.create({"email": "powner@ara.local", "full_name": "POwner", "password_hash": "h"})
    
    project_repo = ProjectRepository(db_session)
    project = project_repo.create({"name": "Repo Project", "owner_id": user.id})
    project_repo.add_member(project.id, user.id, role="owner")

    user_projects = project_repo.get_user_projects(user.id)
    assert len(user_projects) == 1
    assert user_projects[0].name == "Repo Project"

    workspace = project_repo.create_workspace(project.id, name="WS 1")
    assert workspace.id is not None
    assert workspace.name == "WS 1"


def test_research_session_repository(db_session):
    user_repo = UserRepository(db_session)
    user = user_repo.create({"email": "res@ara.local", "full_name": "Res User", "password_hash": "h"})

    res_repo = ResearchSessionRepository(db_session)
    session = res_repo.create({"user_id": user.id, "title": "Session 1", "goal": "Goal 1"})
    
    conv = res_repo.create_conversation(session.id, title="Thread 1")
    msg = res_repo.append_message(conv.id, sender="user", content="Hello ARA")

    messages = res_repo.get_conversation_messages(conv.id)
    assert len(messages) == 1
    assert messages[0].content == "Hello ARA"


def test_audit_log_repository(db_session):
    audit_repo = AuditLogRepository(db_session)
    log = audit_repo.record_event(
        action="LOGIN",
        resource_type="USER",
        user_id="usr-123",
        payload={"ip": "127.0.0.1"},
    )
    assert log.id is not None
    assert log.action == "LOGIN"

    audit_repo.set_setting("system.theme", "dark", description="UI theme setting")
    theme = audit_repo.get_setting("system.theme")
    assert theme == "dark"
