"""Tenant Manager — Multi-tenant workspace isolation and resource quota management."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.platform_infra.models.tenant import TenantQuota, TenantSpec, TenantWorkspaceState
from utils.logger import get_logger

logger = get_logger("TenantManager")


class TenantManager:
    """Manages multi-tenant tenant registration, workspace allocation, and resource quota tracking."""

    def __init__(self, base_workspace_dir: Optional[str] = None) -> None:
        if base_workspace_dir is None:
            base_workspace_dir = os.path.join(os.getcwd(), ".tenants")
        self.base_dir = Path(base_workspace_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self._tenants: Dict[str, TenantSpec] = {}
        self._states: Dict[str, TenantWorkspaceState] = {}

        # Register default tenant
        self.register_tenant(
            TenantSpec(tenant_id="default_tenant", tenant_name="Default Organization", owner_email="admin@ara.internal")
        )

    def register_tenant(self, tenant: TenantSpec) -> TenantWorkspaceState:
        """Register tenant and allocate isolated workspace directory."""
        self._tenants[tenant.tenant_id] = tenant

        tenant_dir = self.base_dir / tenant.tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)

        state = TenantWorkspaceState(
            tenant_id=tenant.tenant_id,
            workspace_storage_dir=str(tenant_dir.resolve()),
        )
        self._states[tenant.tenant_id] = state
        logger.info(f"TenantManager registered tenant '{tenant.tenant_name}' [{tenant.tenant_id}]")
        return state

    def check_quota(self, tenant_id: str) -> bool:
        """Check if tenant is within allocated resource quota limits."""
        tenant = self._tenants.get(tenant_id)
        state = self._states.get(tenant_id)

        if not tenant or not state:
            return False

        if state.active_workflows_count >= tenant.quota.max_concurrent_workflows:
            logger.warning(f"Tenant '{tenant_id}' exceeded max_concurrent_workflows quota ({tenant.quota.max_concurrent_workflows}).")
            return False

        return True

    def increment_workflow(self, tenant_id: str) -> None:
        """Increment active workflow counter for tenant."""
        state = self._states.get(tenant_id)
        if state:
            state.active_workflows_count += 1

    def decrement_workflow(self, tenant_id: str) -> None:
        """Decrement active workflow counter for tenant."""
        state = self._states.get(tenant_id)
        if state and state.active_workflows_count > 0:
            state.active_workflows_count -= 1

    def get_tenant_state(self, tenant_id: str) -> Optional[TenantWorkspaceState]:
        """Retrieve tenant workspace state."""
        return self._states.get(tenant_id)
