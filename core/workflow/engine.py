"""Autonomous Research Engine Facade — End-to-end autonomous research workflow orchestrator."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from core.collaboration.engine import MultiAgentCollaborationEngine
from core.knowledge_graph.engine import KnowledgeGraphEngine
from core.workflow.components.citation_manager import CitationManager
from core.workflow.components.conflict_analyzer import ConflictAnalyzer
from core.workflow.components.evidence_aggregator import EvidenceAggregator
from core.workflow.components.goal_analyzer import ResearchGoalAnalyzer
from core.workflow.components.question_generator import ResearchQuestionGenerator
from core.workflow.components.report_composer import ReportComposer
from core.workflow.components.workflow_generator import WorkflowGenerator
from core.workflow.components.workflow_monitor import WorkflowMonitor
from core.workflow.models.context import ResearchWorkflowContext, WorkflowStage, WorkflowStatus
from core.workflow.models.report import ResearchReport
from utils.logger import get_logger

logger = get_logger("AutonomousResearchEngine")


class AutonomousResearchEngine:
    """Main facade orchestrating autonomous research planning, multi-agent execution, evidence aggregation, and report composition."""

    def __init__(
        self,
        collab_engine: Optional[MultiAgentCollaborationEngine] = None,
        kg_engine: Optional[KnowledgeGraphEngine] = None,
    ) -> None:
        self.collab_engine = collab_engine or MultiAgentCollaborationEngine()
        self.kg_engine = kg_engine or KnowledgeGraphEngine()

        self.goal_analyzer = ResearchGoalAnalyzer()
        self.question_generator = ResearchQuestionGenerator()
        self.workflow_generator = WorkflowGenerator()
        self.evidence_aggregator = EvidenceAggregator()
        self.conflict_analyzer = ConflictAnalyzer()
        self.citation_manager = CitationManager()
        self.report_composer = ReportComposer()
        self.monitor = WorkflowMonitor()

    def execute_autonomous_research(
        self, query: str, constraints_override: Optional[Dict[str, Any]] = None
    ) -> ResearchWorkflowContext:
        """Execute end-to-end autonomous research workflow for query."""
        start_t = time.time()
        ctx = ResearchWorkflowContext()
        ctx.status = WorkflowStatus.RUNNING

        try:
            # Stage 1: Goal Analysis
            self.monitor.record_stage_start(ctx, WorkflowStage.GOAL_ANALYZED)
            ctx.goal = self.goal_analyzer.analyze_goal(query, constraints_override)
            self.monitor.record_stage_complete(ctx, WorkflowStage.GOAL_ANALYZED)

            # Stage 2: Question Generation
            self.monitor.record_stage_start(ctx, WorkflowStage.QUESTIONS_GENERATED)
            ctx.questions = self.question_generator.generate_questions(ctx.goal)
            ctx.metrics.questions_generated = len(ctx.questions)
            self.monitor.record_stage_complete(ctx, WorkflowStage.QUESTIONS_GENERATED)

            # Stage 3: Workflow Generation
            self.monitor.record_stage_start(ctx, WorkflowStage.WORKFLOW_GENERATED)
            assignments = self.workflow_generator.generate_task_assignments(ctx.goal, ctx.questions)
            self.monitor.record_stage_complete(ctx, WorkflowStage.WORKFLOW_GENERATED)

            # Stage 4: Multi-Agent Execution
            self.monitor.record_stage_start(ctx, WorkflowStage.MULTI_AGENT_EXECUTING)
            collab_ctx = self.collab_engine.execute_assignments(assignments, query=query)
            ctx.metrics.questions_resolved = collab_ctx.metrics.completed_tasks
            self.monitor.record_stage_complete(ctx, WorkflowStage.MULTI_AGENT_EXECUTING)

            # Stage 5: Evidence Aggregation
            self.monitor.record_stage_start(ctx, WorkflowStage.EVIDENCE_AGGREGATED)
            ctx.evidence = self.evidence_aggregator.aggregate_evidence(
                ctx.questions, workspace=self.collab_engine.workspace, kg_engine=self.kg_engine
            )
            ctx.metrics.evidence_records_count = len(ctx.evidence)
            self.monitor.record_stage_complete(ctx, WorkflowStage.EVIDENCE_AGGREGATED)

            # Stage 6: Conflict Analysis
            self.monitor.record_stage_start(ctx, WorkflowStage.CONFLICTS_ANALYZED)
            ctx.conflicts = self.conflict_analyzer.analyze_conflicts(ctx.evidence)
            ctx.metrics.conflicts_detected = len(ctx.conflicts)
            ctx.metrics.conflicts_resolved = sum(1 for c in ctx.conflicts if c.is_resolved)
            self.monitor.record_stage_complete(ctx, WorkflowStage.CONFLICTS_ANALYZED)

            # Stage 7: Citation Management
            self.monitor.record_stage_start(ctx, WorkflowStage.CITATIONS_MANAGED)
            ctx.citations = self.citation_manager.extract_citations_from_evidence(ctx.evidence)
            ctx.metrics.citations_generated = len(ctx.citations)
            self.monitor.record_stage_complete(ctx, WorkflowStage.CITATIONS_MANAGED)

            # Stage 8: Report Composition
            self.monitor.record_stage_start(ctx, WorkflowStage.REPORT_COMPOSED)
            ctx.report = self.report_composer.compose_report(
                goal=ctx.goal,
                questions=ctx.questions,
                evidence=ctx.evidence,
                conflicts=ctx.conflicts,
                citations=ctx.citations,
                workspace=self.collab_engine.workspace,
            )
            self.monitor.record_stage_complete(ctx, WorkflowStage.REPORT_COMPOSED)

            # Finalize Workflow
            total_duration_ms = (time.time() - start_t) * 1000.0
            ctx.metrics.total_latency_ms = total_duration_ms
            ctx.stage = WorkflowStage.COMPLETED
            ctx.status = WorkflowStatus.COMPLETED

            logger.info(
                f"Autonomous Research Workflow [{ctx.session_id}] COMPLETED in {total_duration_ms:.2f}ms. "
                f"Resolved: {ctx.metrics.questions_resolved}/{ctx.metrics.questions_generated} questions."
            )
            return ctx

        except Exception as exc:
            logger.exception(f"Autonomous Research Workflow [{ctx.session_id}] FAILED: {exc}")
            ctx.stage = WorkflowStage.FAILED
            ctx.status = WorkflowStatus.FAILED
            return ctx
