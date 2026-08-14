"""Role-Based Access Control (RBAC) and Permission Resolution Engine."""

from enum import Enum
from typing import List, Set, Union


class RoleEnum(str, Enum):
    ADMIN = "Admin"
    RESEARCHER = "Researcher"
    DEVELOPER = "Developer"
    VIEWER = "Viewer"


class PermissionEnum(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"
    WORKFLOW_MANAGE = "workflow_manage"
    DATASET_MANAGE = "dataset_manage"


ROLE_PERMISSIONS = {
    RoleEnum.ADMIN.value: ["*"],
    RoleEnum.DEVELOPER.value: [
        PermissionEnum.READ.value,
        PermissionEnum.WRITE.value,
        PermissionEnum.EXECUTE.value,
        PermissionEnum.WORKFLOW_MANAGE.value,
        PermissionEnum.DATASET_MANAGE.value,
    ],
    RoleEnum.RESEARCHER.value: [
        PermissionEnum.READ.value,
        PermissionEnum.WRITE.value,
        PermissionEnum.EXECUTE.value,
        "research:*",
        "workspace:*",
    ],
    RoleEnum.VIEWER.value: [
        PermissionEnum.READ.value,
    ],
}


class RBACManager:
    """Production RBAC engine for evaluating roles and granular permissions."""

    @staticmethod
    def get_role_permissions(role_name: str) -> List[str]:
        """Fetch permissions list for a role."""
        return ROLE_PERMISSIONS.get(role_name, [PermissionEnum.READ.value])

    @staticmethod
    def has_role(user_role: str, required_roles: List[Union[str, RoleEnum]]) -> bool:
        """Check if user role matches any required role."""
        req_str_list = [r.value if isinstance(r, RoleEnum) else str(r) for r in required_roles]
        
        # Superuser Admin bypasses role checks
        if user_role == RoleEnum.ADMIN.value:
            return True

        return user_role in req_str_list

    @staticmethod
    def has_permission(user_role: str, user_permissions: List[str], required_permission: str) -> bool:
        """Evaluate if user role or explicit permissions grant a required permission."""
        # 1. Superuser or wildcard check
        if user_role == RoleEnum.ADMIN.value or "*" in user_permissions:
            return True

        # 2. Check role default permissions
        role_perms = RBACManager.get_role_permissions(user_role)
        if "*" in role_perms or required_permission in role_perms:
            return True

        # 3. Check exact user explicit permissions
        if required_permission in user_permissions:
            return True

        # 4. Check prefix wildcard matches (e.g. 'research:*' matches 'research:create')
        if ":" in required_permission:
            prefix = required_permission.split(":")[0] + ":*"
            if prefix in role_perms or prefix in user_permissions:
                return True

        return False
