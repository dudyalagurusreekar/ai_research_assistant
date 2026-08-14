"""Unit test for TenantManager."""

import pytest

from core.platform_infra.components.tenant_manager import TenantManager
from core.platform_infra.models.tenant import TenantQuota, TenantSpec


def test_tenant_manager_isolation_and_quotas(tmp_path):
    manager = TenantManager(base_workspace_dir=str(tmp_path))

    tenant = TenantSpec(
        tenant_id="org_alpha",
        tenant_name="Alpha Corp",
        owner_email="owner@alpha.org",
        quota=TenantQuota(max_concurrent_workflows=2),
    )

    state = manager.register_tenant(tenant)
    assert state.tenant_id == "org_alpha"
    assert manager.check_quota("org_alpha") is True

    manager.increment_workflow("org_alpha")
    manager.increment_workflow("org_alpha")

    # Exceeded quota
    assert manager.check_quota("org_alpha") is False
