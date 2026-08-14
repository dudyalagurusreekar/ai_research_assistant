"""Platform Tool — Enterprise Infrastructure Tool Facade for ToolRegistry."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.platform_infra.engine import PlatformEngine
from utils.logger import get_logger

logger = get_logger("PlatformTool")


class PlatformTool:
    """Tool Registry interface for platform, auth, health check, and disaster recovery actions."""

    def __init__(self, engine: Optional[PlatformEngine] = None) -> None:
        self.engine = engine or PlatformEngine()
        self.name = "platform_tool"
        self.description = "Manages authentication, tenant allocation, plugin SDK, observability metrics, secrets, and disaster recovery snapshots."

    def execute(self, action: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute platform action."""
        logger.info(f"PlatformTool executing action '{action}'")

        if action == "check_health":
            health = self.engine.get_system_health()
            return {"status": "success", "health": health}

        elif action == "audit_auth":
            user_id = kwargs.get("user_id", "usr_admin")
            token = self.engine.auth_manager.issue_jwt_token(user_id)
            return {
                "status": "success",
                "user_id": user_id,
                "token_type": token.token_type,
                "expires_in_seconds": token.expires_in_seconds,
            }

        elif action == "list_tenants":
            tenants = [t.to_dict() for t in self.engine.tenant_manager._tenants.values()]
            return {"status": "success", "tenants_count": len(tenants), "tenants": tenants}

        elif action == "create_backup":
            tenant_id = kwargs.get("tenant_id", "global")
            snapshot = self.engine.disaster_recovery.create_snapshot(tenant_id=tenant_id)
            return {"status": "success", "snapshot": snapshot.to_dict()}

        else:
            return {"status": "error", "message": f"Unsupported action '{action}'"}
