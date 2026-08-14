"""Unit tests for Auth Layer (OAuth2, CredentialVault) and Permission Manager (RBAC/ABAC)."""

import pytest
import os

from tools.integration.auth.credential_vault import CredentialVault
from tools.integration.auth.oauth2_manager import OAuth2Manager, RateLimitHeaderParser
from tools.integration.permissions.permission_manager import PermissionManager, PermissionAction, RolePolicy, AccessScope


def test_credential_vault_encryption():
    vault_path = ".storage/test_vault.json"
    vault = CredentialVault(vault_path=vault_path)
    vault.store_credential("github", "ghp_secret_token_12345")

    retrieved = vault.get_credential("github")
    assert retrieved == "ghp_secret_token_12345"

    if os.path.exists(vault_path):
        os.remove(vault_path)


def test_oauth2_manager():
    vault_path = ".storage/test_oauth_vault.json"
    vault = CredentialVault(vault_path=vault_path)
    mgr = OAuth2Manager(vault=vault)

    mgr.store_token("gmail", access_token="acc_token_999", refresh_token="ref_token_888", expires_in=3600)
    token = mgr.get_token("gmail")
    assert token == "acc_token_999"

    if os.path.exists(vault_path):
        os.remove(vault_path)


def test_rate_limit_header_parser():
    headers = {"X-RateLimit-Limit": "1000", "X-RateLimit-Remaining": "995", "Retry-After": "10"}
    parsed = RateLimitHeaderParser.parse_headers(headers)
    assert parsed["limit"] == 1000
    assert parsed["remaining"] == 995
    assert parsed["retry_after"] == 10


def test_permission_manager_least_privilege():
    pm = PermissionManager()
    pm.assign_role("analyst_agent", "analyst")

    # Analyst has READ & EXECUTE permissions
    assert pm.check_permission("analyst_agent", "gmail", action=PermissionAction.READ) is True
    assert pm.check_permission("analyst_agent", "gmail", action=PermissionAction.EXECUTE) is True

    # Analyst does NOT have DELETE or ADMIN permission by default
    assert pm.check_permission("analyst_agent", "gmail", action=PermissionAction.DELETE) is False
    assert pm.check_permission("analyst_agent", "gmail", action=PermissionAction.ADMIN) is False

    # Admin has all permissions
    pm.assign_role("admin_agent", "admin")
    assert pm.check_permission("admin_agent", "gmail", action=PermissionAction.DELETE) is True
