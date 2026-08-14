import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from infrastructure.database.connection import DatabaseManager
from infrastructure.database.models import (
    Base,
    User,
    Role,
    UserRole,
    Project,
    Workspace,
    ResearchSession,
    Conversation,
    Message,
    Document,
    DocumentChunk,
    Report,
    BrowserSession,
    Workflow,
    WorkflowExecution,
    ConnectorConfig,
    BenchmarkRun,
    SystemSetting,
)


@pytest.fixture
def db_session():
    """In-memory SQLite database session fixture for isolated model tests."""
    manager = DatabaseManager("sqlite:///:memory:")
    manager.create_all_tables(Base)
    with manager.get_session() as session:
        yield session
    manager.drop_all_tables(Base)


def test_user_model_creation_and_soft_delete(db_session):
    user = User(
        email="test@ara.local",
        full_name="Test User",
        password_hash="secret_hash",
    )
    db_session.add(user)
    db_session.flush()

    assert user.id is not None
    assert len(user.id) == 36
    assert user.created_at is not None
    assert user.is_deleted is False
    assert user.deleted_at is None

    # Test soft delete mixin
    user.soft_delete()
    db_session.flush()

    assert user.is_deleted is True
    assert user.deleted_at is not None

    # Test restore mixin
    user.restore()
    db_session.flush()
    assert user.is_deleted is False


def test_user_roles_relationship(db_session):
    user = User(email="role_user@ara.local", full_name="Role User", password_hash="hash")
    role = Role(name="Admin", permissions=["*"])
    db_session.add_all([user, role])
    db_session.flush()

    user_role = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(user_role)
    db_session.flush()

    assert len(user.user_roles) == 1
    assert user.user_roles[0].role.name == "Admin"


def test_project_and_workspace_hierarchy(db_session):
    user = User(email="owner@ara.local", full_name="Owner", password_hash="hash")
    db_session.add(user)
    db_session.flush()

    project = Project(name="AI Research Project", owner_id=user.id)
    db_session.add(project)
    db_session.flush()

    workspace = Workspace(project_id=project.id, name="NLP Workspace")
    db_session.add(workspace)
    db_session.flush()

    assert workspace.project.name == "AI Research Project"
    assert len(project.workspaces) == 1


def test_research_session_and_messages(db_session):
    user = User(email="researcher@ara.local", full_name="Researcher", password_hash="hash")
    db_session.add(user)
    db_session.flush()

    session = ResearchSession(user_id=user.id, title="Gene Editing Study", goal="Literature review")
    db_session.add(session)
    db_session.flush()

    conv = Conversation(session_id=session.id, title="CRISPR Thread")
    db_session.add(conv)
    db_session.flush()

    msg = Message(conversation_id=conv.id, sender="user", content="Explain Cas9 specificity")
    db_session.add(msg)
    db_session.flush()

    assert msg.conversation.title == "CRISPR Thread"
    assert len(conv.messages) == 1


def test_workflow_and_execution_models(db_session):
    user = User(email="test@ara-research.org", full_name="Test User", password_hash="hash")
    db_session.add(user)
    db_session.flush()

    res_session = ResearchSession(user_id=user.id, title="WF Session", goal="Automation")
    wf = Workflow(name="Multi-step Research DAG", dag_definition={"nodes": ["step1", "step2"]})
    db_session.add_all([res_session, wf])
    db_session.flush()

    execution = WorkflowExecution(
        workflow_id=wf.id,
        research_session_id=res_session.id,
        status="running",
        total_steps=2,
    )
    db_session.add(execution)
    db_session.flush()

    assert execution.workflow.name == "Multi-step Research DAG"
    assert execution.research_session.title == "WF Session"
