"""Auth models — Authentication, Authorization, JWT, API Keys, and RBAC roles."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class UserRole(Enum):
    """Role-Based Access Control (RBAC) user roles."""

    ADMIN = "admin"
    RESEARCHER = "researcher"
    VIEWER = "viewer"


class AuthType(Enum):
    """Authentication methods supported by Platform AuthManager."""

    JWT = "jwt"
    API_KEY = "api_key"
    OAUTH = "oauth"


@dataclass
class UserIdentity:
    """User Identity representation across platform tenants."""

    user_id: str
    username: str
    email: str
    role: UserRole = UserRole.RESEARCHER
    tenant_id: str = "default_tenant"
    is_active: bool = True
    permissions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.permissions:
            if self.role == UserRole.ADMIN:
                self.permissions = ["read", "write", "execute", "admin", "delete"]
            elif self.role == UserRole.RESEARCHER:
                self.permissions = ["read", "write", "execute"]
            else:
                self.permissions = ["read"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "tenant_id": self.tenant_id,
            "is_active": self.is_active,
            "permissions": self.permissions,
        }


@dataclass
class JWTToken:
    """JWT Token bearer container."""

    access_token: str
    token_type: str = "Bearer"
    expires_in_seconds: int = 3600
    issued_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class APIKey:
    """Platform API Key record."""

    key_id: str = field(default_factory=lambda: f"key_{uuid.uuid4().hex[:8]}")
    key_hash: str = ""
    name: str = "Default API Key"
    user_id: str = ""
    tenant_id: str = "default_tenant"
    role: UserRole = UserRole.RESEARCHER
    is_revoked: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AuthContext:
    """Authenticated request session context."""

    user: UserIdentity
    auth_type: AuthType = AuthType.JWT
    token_id: Optional[str] = None
    is_authenticated: bool = True

    def has_permission(self, required_permission: str) -> bool:
        """Check if authenticated identity possesses required permission."""
        return self.is_authenticated and (
            "admin" in self.user.permissions or required_permission in self.user.permissions
        )
