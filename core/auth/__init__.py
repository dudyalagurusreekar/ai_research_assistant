"""ARA Sprint 2 Authentication & User Management Package."""

from core.auth.password import PasswordHasher, PasswordPolicyValidator
from core.auth.jwt import jwt_manager, JWTManager
from core.auth.rbac import RoleEnum, PermissionEnum, RBACManager
from core.auth.email_service import email_service, EmailService, MockEmailProvider
from core.auth.oauth import oauth_manager, OAuthManager
from core.auth.service import AuthService
from core.auth.dependencies import get_current_user, require_roles, require_permissions

__all__ = [
    "PasswordHasher",
    "PasswordPolicyValidator",
    "jwt_manager",
    "JWTManager",
    "RoleEnum",
    "PermissionEnum",
    "RBACManager",
    "email_service",
    "EmailService",
    "MockEmailProvider",
    "oauth_manager",
    "OAuthManager",
    "AuthService",
    "get_current_user",
    "require_roles",
    "require_permissions",
]
