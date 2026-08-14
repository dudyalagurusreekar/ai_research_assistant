"""Database Seeder populating default roles, system admin, system settings, and sample workspace."""

import sys
import os
import uuid
from typing import Optional
from sqlalchemy.orm import Session

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from infrastructure.database.connection import db_manager
from infrastructure.database.models import (
    Base,
    User,
    Role,
    UserRole,
    Project,
    Workspace,
    ResearchSession,
    Conversation,
    ConnectorConfig,
    SystemSetting,
)
from utils.logger import get_logger

logger = get_logger("DatabaseSeeder")


def seed_database(session: Optional[Session] = None) -> None:
    """Populate database with initial default roles, admin user, and system settings."""
    should_close = False
    if session is None:
        db_manager.create_all_tables(Base)
        session = db_manager.SessionLocal()
        should_close = True

    try:
        logger.info("Starting database seed script...")

        # 1. Seed Default System Roles
        roles_data = [
            {"name": "Admin", "description": "Full administrative permissions", "permissions": ["*"]},
            {"name": "Researcher", "description": "Autonomous research and execution rights", "permissions": ["research:*", "workspace:*"]},
            {"name": "Viewer", "description": "Read-only access to reports and graphs", "permissions": ["read:*"]},
        ]
        
        roles_map = {}
        for r_info in roles_data:
            role = session.query(Role).filter(Role.name == r_info["name"]).first()
            if not role:
                role = Role(
                    name=r_info["name"],
                    description=r_info["description"],
                    permissions=r_info["permissions"],
                )
                session.add(role)
                session.flush()
                logger.info(f"Seeded role: {r_info['name']}")
            roles_map[r_info["name"]] = role

        # 2. Seed Default Admin User
        admin_email = "admin@ara-research.org"
        admin_user = session.query(User).filter(User.email == admin_email).first()
        if not admin_user:
            admin_user = User(
                email=admin_email,
                full_name="System Administrator",
                password_hash="pbkdf2_sha256$hashed_admin_password_sprint_1",
                is_active=True,
                is_superuser=True,
                tenant_id="tenant-default-001",
            )
            session.add(admin_user)
            session.flush()
            
            # Associate Admin Role
            user_role = UserRole(user_id=admin_user.id, role_id=roles_map["Admin"].id)
            session.add(user_role)
            logger.info(f"Seeded default admin user: {admin_email}")

        # 3. Seed Default System Settings
        settings_data = [
            ("platform.name", "AI Research Assistant", "Platform display name", True),
            ("platform.version", "1.0.0", "Current platform version", True),
            ("storage.default_bucket", "ara-uploads", "Default upload bucket", False),
            ("rag.vector_dim", "1536", "Vector embedding dimensionality", True),
        ]
        for key, val, desc, pub in settings_data:
            setting = session.query(SystemSetting).filter(SystemSetting.key == key).first()
            if not setting:
                setting = SystemSetting(key=key, value=val, description=desc, is_public=pub)
                session.add(setting)

        # 4. Seed Default Sample Project & Workspace
        project = session.query(Project).filter(Project.name == "Default Enterprise Research Project").first()
        if not project:
            project = Project(
                name="Default Enterprise Research Project",
                description="Default workspace project for initial research sessions",
                owner_id=admin_user.id,
                tenant_id="tenant-default-001",
                visibility="shared",
            )
            session.add(project)
            session.flush()

            workspace = Workspace(
                project_id=project.id,
                name="General Workspace",
                description="Default workspace for RAG documents and knowledge graphs",
            )
            session.add(workspace)
            session.flush()
            logger.info("Seeded default project and workspace.")

            # Sample Research Session
            res_session = ResearchSession(
                user_id=admin_user.id,
                project_id=project.id,
                title="Initial Platform Verification Research",
                goal="Verify database foundation and infrastructure layers",
                status="completed",
            )
            session.add(res_session)
            session.flush()

            conversation = Conversation(
                session_id=res_session.id,
                title="Verification Thread",
                model_name="gemini-2.5-pro",
            )
            session.add(conversation)

        # 5. Seed Default Connectors
        connectors_data = [
            ("Gmail Connector", "gmail"),
            ("GitHub Connector", "github"),
            ("Slack Connector", "slack"),
        ]
        for c_name, c_type in connectors_data:
            conn = session.query(ConnectorConfig).filter(ConnectorConfig.name == c_name).first()
            if not conn:
                conn = ConnectorConfig(name=c_name, connector_type=c_type, is_enabled=True)
                session.add(conn)

        session.commit()
        logger.info("Database seeding completed successfully.")

    except Exception as exc:
        session.rollback()
        logger.error(f"Error during database seed: {exc}")
        raise
    finally:
        if should_close:
            session.close()


if __name__ == "__main__":
    seed_database()
