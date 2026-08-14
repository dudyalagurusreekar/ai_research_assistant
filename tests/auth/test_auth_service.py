"""Integration tests for AuthService orchestration."""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from infrastructure.database.connection import DatabaseManager
from infrastructure.database.models import Base
from core.auth.service import AuthService


@pytest.fixture
def db_session():
    manager = DatabaseManager("sqlite:///:memory:")
    manager.create_all_tables(Base)
    with manager.get_session() as session:
        yield session
    manager.drop_all_tables(Base)


def test_auth_service_registration_and_login(db_session):
    auth_service = AuthService(db_session)
    
    # 1. Register User
    user, verify_token = auth_service.register_user(
        email="test_svc@ara-research.org",
        password="SecurePassword123!",
        full_name="Service Test User",
        role_name="Researcher",
    )
    assert user.id is not None
    assert user.email == "test_svc@ara-research.org"
    assert verify_token is not None

    # 2. Login User
    logged_user, tokens = auth_service.login_user("test_svc@ara-research.org", "SecurePassword123!")
    assert logged_user.id == user.id
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # 3. Refresh Tokens
    new_tokens = auth_service.refresh_access_token(tokens["refresh_token"])
    assert "access_token" in new_tokens
    assert new_tokens["access_token"] != tokens["access_token"]

    # 4. Logout User
    success = auth_service.logout_user(new_tokens["access_token"])
    assert success is True


def test_auth_service_login_failed_attempts_and_lockout(db_session):
    auth_service = AuthService(db_session)
    auth_service.register_user(
        email="lockout@ara-research.org",
        password="SecurePassword123!",
        full_name="Lockout User",
    )

    # Fail login 5 times to trigger lockout
    for _ in range(5):
        with pytest.raises(ValueError):
            auth_service.login_user("lockout@ara-research.org", "WrongPassword123!")

    # 6th login attempt must be rejected with lockout PermissionError
    with pytest.raises(PermissionError) as exc_info:
        auth_service.login_user("lockout@ara-research.org", "SecurePassword123!")

    assert "locked" in str(exc_info.value).lower()


def test_auth_service_password_reset_flow(db_session):
    auth_service = AuthService(db_session)
    user, _ = auth_service.register_user(
        email="reset@ara-research.org",
        password="OldPassword123!",
        full_name="Reset User",
    )

    # 1. Forgot password
    auth_service.forgot_password("reset@ara-research.org")

    # Generate token directly for testing reset
    from core.auth.jwt import jwt_manager
    reset_token = jwt_manager.create_password_reset_token(user.id, user.email)

    # 2. Reset password
    success = auth_service.reset_password(reset_token, "NewPassword123!")
    assert success is True

    # Login with new password
    logged_user, tokens = auth_service.login_user("reset@ara-research.org", "NewPassword123!")
    assert logged_user.id == user.id

    # 3. Token cannot be re-used (single-use constraint)
    with pytest.raises(ValueError) as exc_info:
        auth_service.reset_password(reset_token, "AnotherPassword123!")
    assert "already been used" in str(exc_info.value)
