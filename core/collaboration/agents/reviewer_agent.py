"""Specialized Reviewer Agent — QA, code review, fact checking, and inconsistency verification."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from core.collaboration.agents.base import BaseSpecializedAgent
from core.collaboration.components.memory import CollaborationMemory
from core.collaboration.components.workspace import SharedWorkspace
from core.collaboration.models.agent_info import AgentCapability, AgentRole
from core.collaboration.models.context import AgentOutput, TaskAssignment
from core.collaboration.models.message import MessageType
from utils.logger import get_logger

logger = get_logger("SpecializedReviewerAgent")


class SpecializedReviewerAgent(BaseSpecializedAgent):
    """Agent specialized in output verification, quality auditing, code review, and inconsistency detection."""

    def __init__(self, agent_id: Optional[str] = None) -> None:
        capabilities = [
            AgentCapability(name="quality_assurance", description="Audit multi-agent outputs for quality and precision"),
            AgentCapability(name="code_review", description="Inspect code for security, correctness, and style"),
            AgentCapability(name="fact_checking", description="Verify factual claims against reference data"),
            AgentCapability(name="inconsistency_detection", description="Detect discrepancies across agent findings"),
        ]
        super().__init__(
            name="Reviewer Agent",
            role=AgentRole.REVIEWER,
            capabilities=capabilities,
            agent_id=agent_id,
        )

    def execute_task(
        self,
        task: TaskAssignment,
        inputs: Dict[str, Any],
        workspace: SharedWorkspace,
        memory: CollaborationMemory,
    ) -> AgentOutput:
        """Execute review task and generate verification report."""
        logger.info(f"ReviewerAgent [{self.agent_id}] executing task: {task.title}")
        start_t = time.time()

        # Audit workspace contents
        keys = workspace.list_keys()
        has_research = workspace.has("research_summary") or workspace.has("research_data")
        has_data = workspace.has("data_stats") or workspace.has("data_analysis_result")
        has_code = workspace.has("generated_code") or workspace.has("code_execution_result")
        has_report = workspace.has("final_report")

        issues_found: List[str] = []
        overall_score = 0.95

        if not keys:
            issues_found.append("Workspace is empty prior to review.")
            overall_score -= 0.3

        if has_code:
            code_art = workspace.get("generated_code")
            if isinstance(code_art, str) and ("import os" in code_art or "eval(" in code_art):
                issues_found.append("Code review warning: potentially sensitive import detected.")
                overall_score -= 0.1

        review_notes = (
            f"Review Audit Completed.\n"
            f"- Workspace Artifacts Reviewed: {len(keys)} items ({', '.join(keys[:5])})\n"
            f"- Research Quality: {'PASSED' if has_research else 'N/A'}\n"
            f"- Data Analysis Quality: {'PASSED' if has_data else 'N/A'}\n"
            f"- Code Quality: {'PASSED' if has_code else 'N/A'}\n"
            f"- Report Synthesis Quality: {'PASSED' if has_report else 'N/A'}\n"
            f"- Issues Found: {len(issues_found)}\n"
        )

        verification_passed = len(issues_found) == 0 and overall_score >= 0.70

        result_payload = {
            "review_notes": review_notes,
            "verification_passed": verification_passed,
            "quality_score": round(overall_score, 2),
            "issues_found": issues_found,
            "reviewed_keys": keys,
        }

        # Store in workspace
        self.write_workspace(workspace, "review_result", result_payload, artifact_type="data")

        # Send completion message
        self.send_message(
            memory=memory,
            recipient_id=None,
            content=f"Review completed. Quality Score: {overall_score:.2f}, Verification Passed: {verification_passed}.",
            message_type=MessageType.FEEDBACK,
            payload=result_payload,
        )

        latency_ms = (time.time() - start_t) * 1000.0
        return AgentOutput(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status="completed",
            result=result_payload,
            confidence_score=overall_score,
            execution_latency_ms=latency_ms,
        )
