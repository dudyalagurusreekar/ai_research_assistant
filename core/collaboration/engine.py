"""Multi-Agent Collaboration Engine Facade — Main entry point for multi-agent workflows."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from core.collaboration.agents.code_agent import SpecializedCodeAgent
from core.collaboration.agents.data_agent import SpecializedDataAgent
from core.collaboration.agents.research_agent import SpecializedResearchAgent
from core.collaboration.agents.reviewer_agent import SpecializedReviewerAgent
from core.collaboration.agents.writer_agent import SpecializedWriterAgent
from core.collaboration.components.conflict_resolution import ConflictResolutionEngine
from core.collaboration.components.memory import CollaborationMemory
from core.collaboration.components.orchestrator import MultiAgentOrchestrator
from core.collaboration.components.registry import AgentRegistry
from core.collaboration.components.workspace import SharedWorkspace
from core.collaboration.models.agent_info import AgentRole
from core.collaboration.models.context import (
    CollaborationContext,
    CollaborationStatus,
    ExecutionMode,
    TaskAssignment,
)
from utils.logger import get_logger

logger = get_logger("MultiAgentCollaborationEngine")


class MultiAgentCollaborationEngine:
    """Main facade for ARA Version 2.5 Multi-Agent Collaboration Framework."""

    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        workspace: Optional[SharedWorkspace] = None,
        memory: Optional[CollaborationMemory] = None,
        auto_register_default_agents: bool = True,
    ) -> None:
        self.registry = registry or AgentRegistry.get_instance()
        self.workspace = workspace or SharedWorkspace()
        self.memory = memory or CollaborationMemory()
        self.conflict_engine = ConflictResolutionEngine()
        self.orchestrator = MultiAgentOrchestrator(
            registry=self.registry,
            workspace=self.workspace,
            memory=self.memory,
            conflict_engine=self.conflict_engine,
        )

        if auto_register_default_agents:
            self._ensure_default_agents_registered()

    def _ensure_default_agents_registered(self) -> None:
        """Register the 5 core specialized agents if not already present."""
        if not self.registry.list_agents(role=AgentRole.RESEARCH):
            self.registry.register_agent(SpecializedResearchAgent())
        if not self.registry.list_agents(role=AgentRole.DATA):
            self.registry.register_agent(SpecializedDataAgent())
        if not self.registry.list_agents(role=AgentRole.CODE):
            self.registry.register_agent(SpecializedCodeAgent())
        if not self.registry.list_agents(role=AgentRole.WRITER):
            self.registry.register_agent(SpecializedWriterAgent())
        if not self.registry.list_agents(role=AgentRole.REVIEWER):
            self.registry.register_agent(SpecializedReviewerAgent())

    def create_collaboration_session(
        self, query: str, intent: str = "multi_step_research", mode: ExecutionMode = ExecutionMode.HYBRID
    ) -> CollaborationContext:
        """Initialize a new collaboration context."""
        return CollaborationContext(
            query=query,
            intent=intent,
            execution_mode=mode,
            shared_workspace_id=self.workspace.workspace_id,
        )

    def execute_assignments(
        self, assignments: List[TaskAssignment], query: str = "", context: Optional[CollaborationContext] = None
    ) -> CollaborationContext:
        """Execute a list of task assignments using the multi-agent orchestrator."""
        ctx = context or self.create_collaboration_session(query=query)
        ctx.task_assignments = assignments
        return self.orchestrator.execute_collaboration(ctx)

    def execute_preset_workflow(
        self, workflow_name: str, query: str, payload: Optional[Dict[str, Any]] = None
    ) -> CollaborationContext:
        """Execute common multi-agent workflow presets.

        Supported workflows:
        - 'research_writer': Research -> Writer
        - 'data_writer': Data -> Writer
        - 'research_data_reviewer': Research + Data (parallel) -> Reviewer
        - 'code_reviewer': Code -> Reviewer
        - 'full_multi_agent': Research + Data (wave 0) -> Code (wave 1) -> Writer (wave 2) -> Reviewer (wave 3)
        """
        payload = payload or {}
        ctx = self.create_collaboration_session(query=query)

        if workflow_name == "research_writer":
            t1 = TaskAssignment(
                title="Conduct Literature & Web Research",
                description=query,
                target_role=AgentRole.RESEARCH,
                parameters=payload,
                parallel_wave=0,
            )
            t2 = TaskAssignment(
                title="Synthesize Research Report",
                description=f"Draft analytical report for {query}",
                target_role=AgentRole.WRITER,
                parameters={"title": query},
                parallel_wave=1,
            )
            ctx.task_assignments = [t1, t2]

        elif workflow_name == "data_writer":
            t1 = TaskAssignment(
                title="Profile & Analyze Dataset",
                description=query,
                target_role=AgentRole.DATA,
                parameters=payload,
                parallel_wave=0,
            )
            t2 = TaskAssignment(
                title="Write Data Intelligence Report",
                description=f"Compile dataset findings for {query}",
                target_role=AgentRole.WRITER,
                parameters={"title": query},
                parallel_wave=1,
            )
            ctx.task_assignments = [t1, t2]

        elif workflow_name == "research_data_reviewer":
            t1 = TaskAssignment(
                title="Execute Domain Research",
                description=query,
                target_role=AgentRole.RESEARCH,
                parameters=payload,
                parallel_wave=0,
            )
            t2 = TaskAssignment(
                title="Execute Data Analytics",
                description=query,
                target_role=AgentRole.DATA,
                parameters=payload,
                parallel_wave=0,
            )
            t3 = TaskAssignment(
                title="Audit Research & Data Findings",
                description=f"Verify outputs for {query}",
                target_role=AgentRole.REVIEWER,
                parameters=payload,
                parallel_wave=1,
            )
            ctx.task_assignments = [t1, t2, t3]

        elif workflow_name == "code_reviewer":
            t1 = TaskAssignment(
                title="Generate & Safe Execute Script",
                description=query,
                target_role=AgentRole.CODE,
                parameters=payload,
                parallel_wave=0,
            )
            t2 = TaskAssignment(
                title="Perform Code Security & Quality Review",
                description=f"Review code for {query}",
                target_role=AgentRole.REVIEWER,
                parameters=payload,
                parallel_wave=1,
            )
            ctx.task_assignments = [t1, t2]

        elif workflow_name == "full_multi_agent":
            t1 = TaskAssignment(
                title="Domain Research",
                description=query,
                target_role=AgentRole.RESEARCH,
                parameters=payload,
                parallel_wave=0,
            )
            t2 = TaskAssignment(
                title="Dataset Analysis & Charting",
                description=query,
                target_role=AgentRole.DATA,
                parameters=payload,
                parallel_wave=0,
            )
            t3 = TaskAssignment(
                title="Algorithmic Code Implementation",
                description=query,
                target_role=AgentRole.CODE,
                parameters=payload,
                parallel_wave=1,
            )
            t4 = TaskAssignment(
                title="Draft Analytical Report",
                description=query,
                target_role=AgentRole.WRITER,
                parameters={"title": query},
                parallel_wave=2,
            )
            t5 = TaskAssignment(
                title="Quality & Fact Audit Review",
                description=query,
                target_role=AgentRole.REVIEWER,
                parameters=payload,
                parallel_wave=3,
            )
            ctx.task_assignments = [t1, t2, t3, t4, t5]

        else:
            raise ValueError(f"Unknown preset workflow name: '{workflow_name}'")

        return self.orchestrator.execute_collaboration(ctx)
