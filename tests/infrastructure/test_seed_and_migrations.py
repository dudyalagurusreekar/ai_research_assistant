import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from infrastructure.database.connection import DatabaseManager
from infrastructure.database.models import Base, Role, SystemSetting, User
from infrastructure.database.seed import seed_database


def test_seed_database_populates_roles_and_admin():
    manager = DatabaseManager("sqlite:///:memory:")
    manager.create_all_tables(Base)

    with manager.get_session() as session:
        seed_database(session=session)

        # Check roles
        roles = session.query(Role).all()
        role_names = [r.name for r in roles]
        assert "Admin" in role_names
        assert "Researcher" in role_names
        assert "Viewer" in role_names

        # Check admin user
        admin = session.query(User).filter(User.email == "admin@ara-research.org").first()

        assert admin is not None
        assert admin.is_superuser is True

        # Check settings
        setting = session.query(SystemSetting).filter(SystemSetting.key == "platform.name").first()
        assert setting is not None
        assert setting.value == "AI Research Assistant"
