"""Unit tests for Role-Based Access Control (RBAC) and Permission Resolution."""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from core.auth.rbac import RoleEnum, PermissionEnum, RBACManager


def test_rbac_role_permissions_assignment():
    admin_perms = RBACManager.get_role_permissions(RoleEnum.ADMIN.value)
    assert "*" in admin_perms

    researcher_perms = RBACManager.get_role_permissions(RoleEnum.RESEARCHER.value)
    assert PermissionEnum.READ.value in researcher_perms
    assert "research:*" in researcher_perms

    viewer_perms = RBACManager.get_role_permissions(RoleEnum.VIEWER.value)
    assert viewer_perms == [PermissionEnum.READ.value]


def test_rbac_has_role():
    assert RBACManager.has_role("Admin", [RoleEnum.ADMIN.value]) is True
    # Admin superuser bypasses specific role requirement
    assert RBACManager.has_role("Admin", [RoleEnum.RESEARCHER.value]) is True
    
    assert RBACManager.has_role("Researcher", [RoleEnum.RESEARCHER.value, RoleEnum.DEVELOPER.value]) is True
    assert RBACManager.has_role("Viewer", [RoleEnum.ADMIN.value]) is False


def test_rbac_has_permission():
    # Admin has all permissions
    assert RBACManager.has_permission("Admin", [], "delete_database") is True
    
    # Researcher has research wildcard permissions
    assert RBACManager.has_permission("Researcher", [], "research:create") is True
    assert RBACManager.has_permission("Researcher", [], "admin:delete_user") is False

    # Viewer has read only
    assert RBACManager.has_permission("Viewer", [], "read") is True
    assert RBACManager.has_permission("Viewer", [], "write") is False
