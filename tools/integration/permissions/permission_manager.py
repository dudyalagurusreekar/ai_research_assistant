"""PermissionManager, AccessScope, and AuditLogger for least-privilege security."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
import time

from infrastructure.logging.logger import StructuredLogger


class PermissionAction(str, Enum):
    """Supported operation actions for access evaluation."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


@dataclass
class AccessScope:
    """Represents fine-grained access scope for service connectors."""
    service_name: str
    resource: str = "*"
    actions: Set[PermissionAction] = field(default_factory=lambda: {PermissionAction.READ})

    def matches(self, target_service: str, target_resource: str, action: PermissionAction) -> bool:
        """Check whether scope satisfies target resource and action."""
        service_match = self.service_name in ["*", target_service.lower()]
        resource_match = self.resource in ["*", target_resource.lower()]
        action_match = action in self.actions or PermissionAction.ADMIN in self.actions
        return service_match and resource_match and action_match


@dataclass
class RolePolicy:
    """RBAC Role policy defining granted access scopes."""
    role_name: str
    scopes: List[AccessScope] = field(default_factory=list)


class AuditLogger:
    """Audit logger tracking all permission checks, decisions, and access violations."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("AuditLogger")
        self.logs: List[Dict[str, Any]] = []

    def log_decision(
        self,
        principal: str,
        service: str,
        resource: str,
        action: str,
        allowed: bool,
        reason: str = "",
    ) -> None:
        """Record permission evaluation event."""
        entry = {
            "timestamp": time.time(),
            "principal": principal,
            "service": service,
            "resource": resource,
            "action": action,
            "allowed": allowed,
            "reason": reason,
        }
        self.logs.append(entry)
        if allowed:
            self._logger.info(f"AUDIT PERMISSION GRANTED: [{principal}] -> {service}:{resource}:{action}")
        else:
            self._logger.warning(f"AUDIT PERMISSION DENIED: [{principal}] -> {service}:{resource}:{action} ({reason})")


class PermissionManager:
    """Least-privilege RBAC/ABAC permission evaluator and security manager."""

    def __init__(self, audit_logger: Optional[AuditLogger] = None) -> None:
        self._logger = StructuredLogger("PermissionManager")
        self._audit_logger = audit_logger or AuditLogger()
        self._roles: Dict[str, RolePolicy] = {}
        self._principal_roles: Dict[str, Set[str]] = {}
        self._initialize_default_roles()

    def _initialize_default_roles(self) -> None:
        """Initialize default Admin, Analyst, and ReadOnly roles."""
        admin_role = RolePolicy(
            role_name="admin",
            scopes=[AccessScope(service_name="*", resource="*", actions={PermissionAction.ADMIN})],
        )
        read_only_role = RolePolicy(
            role_name="readonly",
            scopes=[AccessScope(service_name="*", resource="*", actions={PermissionAction.READ})],
        )
        analyst_role = RolePolicy(
            role_name="analyst",
            scopes=[
                AccessScope(service_name="*", resource="*", actions={PermissionAction.READ, PermissionAction.EXECUTE}),
            ],
        )
        self.register_role(admin_role)
        self.register_role(read_only_role)
        self.register_role(analyst_role)

    def register_role(self, role: RolePolicy) -> None:
        """Register custom role policy."""
        self._roles[role.role_name.lower()] = role

    def assign_role(self, principal: str, role_name: str) -> None:
        """Assign role to principal (user/agent)."""
        p = principal.lower()
        if p not in self._principal_roles:
            self._principal_roles[p] = set()
        self._principal_roles[p].add(role_name.lower())

    def check_permission(
        self,
        principal: str,
        service_name: str,
        resource: str = "*",
        action: PermissionAction = PermissionAction.READ,
    ) -> bool:
        """Evaluate least-privilege permission for principal against service operation."""
        p = principal.lower()
        assigned_roles = self._principal_roles.get(p, {"readonly"})

        for role_name in assigned_roles:
            role = self._roles.get(role_name)
            if not role:
                continue
            for scope in role.scopes:
                if scope.matches(target_service=service_name, target_resource=resource, action=action):
                    self._audit_logger.log_decision(principal, service_name, resource, action.value, allowed=True)
                    return True

        self._audit_logger.log_decision(
            principal, service_name, resource, action.value, allowed=False, reason="No matching role scope found"
        )
        return False
