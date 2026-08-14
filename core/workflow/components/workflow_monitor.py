"""Workflow Monitor — Real-time progress monitoring, stage tracking, and latency audit."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from core.workflow.models.context import ResearchWorkflowContext, WorkflowStage, WorkflowStatus
from utils.logger import get_logger

logger = get_logger("WorkflowMonitor")


class WorkflowMonitor:
    """Monitors real-time autonomous workflow state transitions, stage latencies, and token budgets."""

    def __init__(self) -> None:
        self._stage_timestamps: Dict[str, float] = {}

    def record_stage_start(self, ctx: ResearchWorkflowContext, stage: WorkflowStage) -> None:
        """Log stage initiation."""
        ctx.stage = stage
        self._stage_timestamps[stage.value] = time.time()
        logger.info(f"WorkflowMonitor [{ctx.session_id}] Entering Stage: {stage.value}")

    def record_stage_complete(self, ctx: ResearchWorkflowContext, stage: WorkflowStage) -> float:
        """Log stage completion and update total latency."""
        start_t = self._stage_timestamps.get(stage.value, time.time())
        latency_ms = (time.time() - start_t) * 1000.0
        ctx.metrics.total_latency_ms += latency_ms
        logger.info(f"WorkflowMonitor [{ctx.session_id}] Completed Stage: {stage.value} in {latency_ms:.2f}ms")
        return latency_ms

    def audit_status(self, ctx: ResearchWorkflowContext) -> Dict[str, Any]:
        """Audit active workflow status metrics."""
        return {
            "session_id": ctx.session_id,
            "current_stage": ctx.stage.value,
            "status": ctx.status.value,
            "latency_ms": ctx.metrics.total_latency_ms,
            "resolution_rate": ctx.metrics.resolution_rate,
        }
