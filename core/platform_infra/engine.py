"""Platform Engine Facade — Main Enterprise Infrastructure Orchestrator."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from core.platform_infra.components.api_gateway import APIGateway
from core.platform_infra.components.auth_manager import AuthManager
from core.platform_infra.components.disaster_recovery import DisasterRecoveryManager
from core.platform_infra.components.observability_manager import ObservabilityManager
from core.platform_infra.components.plugin_sdk import PluginSDKManager
from core.platform_infra.components.secrets_manager import SecretsManager
from core.platform_infra.components.tenant_manager import TenantManager
from core.platform_infra.models.context import PlatformContext
from utils.logger import get_logger

logger = get_logger("PlatformEngine")


class PlatformEngine:
    """Main enterprise platform facade orchestrating auth, multi-tenancy, gateway, observability, and security."""

    def __init__(self) -> None:
        self.auth_manager = AuthManager()
        self.tenant_manager = TenantManager()
        self.api_gateway = APIGateway(auth_manager=self.auth_manager)
        self.plugin_sdk = PluginSDKManager()
        self.observability = ObservabilityManager()
        self.secrets = SecretsManager()
        self.disaster_recovery = DisasterRecoveryManager()

    def create_context(
        self, user_id: str = "usr_admin", tenant_id: str = "default_tenant"
    ) -> PlatformContext:
        """Create authenticated platform context for user session."""
        user = self.auth_manager._users.get(user_id)
        if not user:
            user = self.auth_manager._users["usr_admin"]

        auth_ctx = self.auth_manager.verify_jwt_token(
            self.auth_manager.issue_jwt_token(user.user_id).access_token
        )
        ctx = PlatformContext(tenant_id=tenant_id, auth_ctx=auth_ctx)

        self.observability.record_counter("platform_sessions_total", 1.0, {"tenant_id": tenant_id})
        logger.info(f"PlatformEngine created context for session '{ctx.session_id}' [User: {user.username}]")
        return ctx

    def get_system_health(self) -> Dict[str, Any]:
        """Audit platform component health and return readiness checks."""
        return {
            "liveness": self.observability.get_liveness(),
            "readiness": self.observability.get_readiness(),
            "tenants_count": len(self.tenant_manager._tenants),
            "plugins_count": len(self.plugin_sdk._plugins),
        }
