"""Production Readiness & Operational Health Verification Test Suite."""

import asyncio

from infrastructure.deployment.health import HealthCheckManager
from tools.registry import registry


def test_health_check_manager_liveness():
    """Verify Liveness health check probe."""
    async def _test():
        health_mgr = HealthCheckManager()
        liveness = await health_mgr.get_liveness()

        assert liveness.status == "healthy"
        assert liveness.version == "1.0.0"

    asyncio.run(_test())


def test_health_check_manager_readiness_all_pillars():
    """Verify Readiness health check probe across all 11 platform pillars."""
    async def _test():
        health_mgr = HealthCheckManager()
        readiness = await health_mgr.get_readiness()

        assert readiness.status == "healthy"
        assert len(readiness.subsystems) == 11

        sub_names = [s.subsystem_name for s in readiness.subsystems]
        assert "core_foundation" in sub_names
        assert "shared_infrastructure" in sub_names
        assert "browser_tool" in sub_names
        assert "document_platform" in sub_names
        assert "search_platform" in sub_names
        assert "memory_platform" in sub_names
        assert "code_platform" in sub_names
        assert "vision_platform" in sub_names
        assert "integration_platform" in sub_names
        assert "workflow_engine" in sub_names
        assert "report_platform" in sub_names

    asyncio.run(_test())


def test_health_check_manager_diagnostics():
    """Verify system telemetry diagnostics endpoint."""
    async def _test():
        health_mgr = HealthCheckManager()
        diag = await health_mgr.get_diagnostics()

        assert "health" in diag
        assert diag["environment"] == "production"
        assert diag["health"]["status"] == "healthy"

    asyncio.run(_test())


def test_global_tool_registry_production_completeness():
    """Verify that all 11 platform tool facades are registered in global ToolRegistry."""
    registered_names = registry.list_tools()
    required_tools = [
        "browser_tool",
        "document_tool",
        "search_tool",
        "memory_tool",
        "code_tool",
        "vision_tool",
        "integration_tool",
        "workflow_tool",
        "report_tool",
    ]

    for req_t in required_tools:
        assert req_t in registered_names, f"Tool '{req_t}' missing from global ToolRegistry!"
