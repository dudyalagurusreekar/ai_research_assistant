"""Unit test for AuthManager."""

import pytest

from core.platform_infra.components.auth_manager import AuthManager
from core.platform_infra.models.auth import UserIdentity, UserRole


def test_auth_manager_jwt_and_api_keys():
    manager = AuthManager()

    # Issue JWT token
    token = manager.issue_jwt_token("usr_admin")
    assert token.access_token is not None

    # Verify JWT token
    auth_ctx = manager.verify_jwt_token(token.access_token)
    assert auth_ctx.user.username == "admin"
    assert auth_ctx.user.role == UserRole.ADMIN

    # Issue & Verify API Key
    raw_key = manager.create_api_key("usr_researcher", "Researcher Key")
    key_ctx = manager.verify_api_key(raw_key)
    assert key_ctx.user.username == "researcher"


def test_auth_manager_rbac():
    manager = AuthManager()
    token = manager.issue_jwt_token("usr_viewer")
    auth_ctx = manager.verify_jwt_token(token.access_token)

    assert manager.check_rbac(auth_ctx, "read") is True
    assert manager.check_rbac(auth_ctx, "delete") is False
