"""End-to-End test for Enterprise Platform Workflow."""

import pytest

from core.platform_infra.engine import PlatformEngine
from tools.platform.platform_tool import PlatformTool


def test_e2e_enterprise_platform_engine():
    engine = PlatformEngine()

    health = engine.get_system_health()
    assert health["liveness"]["status"] == "healthy"
    assert health["readiness"]["status"] == "ready"

    ctx = engine.create_context("usr_admin", "default_tenant")
    assert ctx.session_id is not None
    assert ctx.auth_ctx.user.role.value == "admin"

    snapshot = engine.disaster_recovery.create_snapshot("default_tenant", {"state": "active"})
    restored = engine.disaster_recovery.restore_snapshot(snapshot.snapshot_id)
    assert restored["state"] == "active"


def test_e2e_platform_tool_integration():
    tool = PlatformTool()

    health_res = tool.execute("check_health")
    assert health_res["status"] == "success"

    auth_res = tool.execute("audit_auth", user_id="usr_admin")
    assert auth_res["status"] == "success"

    tenants_res = tool.execute("list_tenants")
    assert tenants_res["status"] == "success"
