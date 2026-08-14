"""Platform Subsystem Integration Adapter — Connects Platform Infrastructure with Sprints 1-9 Subsystems."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.platform_infra.engine import PlatformEngine
from utils.logger import get_logger

logger = get_logger("PlatformSubsystemIntegration")


class PlatformSubsystemIntegration:
    """Handoff and wrapper integration connecting enterprise platform controls with core AI engines."""

    def __init__(self, platform_engine: Optional[PlatformEngine] = None) -> None:
        self.platform = platform_engine or PlatformEngine()

    def execute_secured_research_workflow(
        self, query: str, user_id: str = "usr_researcher", tenant_id: str = "default_tenant"
    ) -> Dict[str, Any]:
        """Execute autonomous research workflow through platform quota and auth checks."""
        # 1. Quota check
        if not self.platform.tenant_manager.check_quota(tenant_id):
            raise PermissionError(f"Quota exceeded for tenant '{tenant_id}'.")

        # 2. Context & Metric recording
        ctx = self.platform.create_context(user_id=user_id, tenant_id=tenant_id)
        self.platform.tenant_manager.increment_workflow(tenant_id)

        try:
            from core.workflow.engine import AutonomousResearchEngine

            workflow_engine = AutonomousResearchEngine()
            result_ctx = workflow_engine.execute_autonomous_research(query)

            self.platform.observability.record_counter("secure_workflows_completed_total", 1.0, {"tenant_id": tenant_id})
            logger.info(f"PlatformSubsystemIntegration completed secured workflow for session '{ctx.session_id}'")

            return {
                "status": "success",
                "session_id": result_ctx.session_id,
                "tenant_id": tenant_id,
                "report_title": result_ctx.report.title if result_ctx.report else "",
                "latency_ms": result_ctx.metrics.total_latency_ms,
            }
        finally:
            self.platform.tenant_manager.decrement_workflow(tenant_id)
