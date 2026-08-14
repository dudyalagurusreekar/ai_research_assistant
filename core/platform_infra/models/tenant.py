"""Tenant models — Multi-tenant workspace isolation and resource quotas."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class TenantQuota:
    """Resource limits allocated per tenant."""

    max_concurrent_workflows: int = 10
    max_storage_mb: float = 10240.0  # 10 GB
    max_token_budget_per_day: int = 1000000
    allow_custom_plugins: bool = True


@dataclass
class TenantSpec:
    """Tenant organization record."""

    tenant_id: str
    tenant_name: str
    owner_email: str
    quota: TenantQuota = field(default_factory=TenantQuota)
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "tenant_name": self.tenant_name,
            "owner_email": self.owner_email,
            "is_active": self.is_active,
            "quota": {
                "max_workflows": self.quota.max_concurrent_workflows,
                "storage_mb": self.quota.max_storage_mb,
            },
        }


@dataclass
class TenantWorkspaceState:
    """Isolated runtime memory and storage state container for a tenant."""

    tenant_id: str
    active_workflows_count: int = 0
    used_storage_mb: float = 0.0
    tokens_consumed_today: int = 0
    workspace_storage_dir: str = ""
