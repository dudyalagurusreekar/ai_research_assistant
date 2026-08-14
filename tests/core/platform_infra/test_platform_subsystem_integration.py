"""Integration test for PlatformSubsystemIntegration."""

import pytest

from core.platform_infra.integration import PlatformSubsystemIntegration


def test_platform_subsystem_secured_workflow():
    integration = PlatformSubsystemIntegration()

    res = integration.execute_secured_research_workflow(
        query="Research quantum computing benchmarks",
        user_id="usr_researcher",
        tenant_id="default_tenant",
    )

    assert res["status"] == "success"
    assert res["tenant_id"] == "default_tenant"
    assert res["latency_ms"] >= 0.0
