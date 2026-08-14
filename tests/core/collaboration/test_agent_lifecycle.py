"""Unit tests for agent lifecycle management and execution across all 5 specialized agents."""

import pytest

from core.collaboration.agents import (
    SpecializedCodeAgent,
    SpecializedDataAgent,
    SpecializedResearchAgent,
    SpecializedReviewerAgent,
    SpecializedWriterAgent,
)
from core.collaboration.components.memory import CollaborationMemory
from core.collaboration.components.workspace import SharedWorkspace
from core.collaboration.models.agent_info import AgentRole, AgentStatus
from core.collaboration.models.context import TaskAssignment


def test_research_agent_lifecycle():
    agent = SpecializedResearchAgent()
    assert agent.role == AgentRole.RESEARCH
    assert agent.metadata.status == AgentStatus.IDLE
    assert any(c.name == "web_search" for c in agent.capabilities)

    workspace = SharedWorkspace()
    memory = CollaborationMemory()
    task = TaskAssignment(title="Research AI Benchmark Results", description="Benchmark AI", target_role=AgentRole.RESEARCH)

    output = agent.execute_task(task, {"query": "AI Benchmark Results"}, workspace, memory)
    assert output.status == "completed"
    assert output.confidence_score >= 0.85
    assert workspace.has("research_summary")


def test_data_agent_lifecycle():
    agent = SpecializedDataAgent()
    assert agent.role == AgentRole.DATA
    assert any(c.name == "data_profiling" for c in agent.capabilities)

    workspace = SharedWorkspace()
    memory = CollaborationMemory()
    task = TaskAssignment(title="Profile Performance Data", description="Profile dataset", target_role=AgentRole.DATA)

    output = agent.execute_task(task, {"dataset_name": "perf_test"}, workspace, memory)
    assert output.status == "completed"
    assert workspace.has("data_stats")
    assert workspace.has("chart_svg")


def test_code_agent_lifecycle():
    agent = SpecializedCodeAgent()
    assert agent.role == AgentRole.CODE
    assert any(c.name == "safe_execution" for c in agent.capabilities)

    workspace = SharedWorkspace()
    memory = CollaborationMemory()
    task = TaskAssignment(title="Generate Benchmark Script", description="Generate script", target_role=AgentRole.CODE)

    output = agent.execute_task(task, {}, workspace, memory)
    assert output.status == "completed"
    assert workspace.has("generated_code")


def test_writer_agent_lifecycle():
    agent = SpecializedWriterAgent()
    assert agent.role == AgentRole.WRITER
    assert any(c.name == "report_generation" for c in agent.capabilities)

    workspace = SharedWorkspace()
    workspace.set("research_summary", "Detailed research summary text.")
    workspace.set("data_stats", {"row_count": 100, "quality_score": 0.99})

    memory = CollaborationMemory()
    task = TaskAssignment(title="Synthesize Final Report", description="Draft report", target_role=AgentRole.WRITER)

    output = agent.execute_task(task, {"title": "AI Performance Report"}, workspace, memory)
    assert output.status == "completed"
    assert workspace.has("final_report")
    assert "AI Performance Report" in workspace.get("final_report")


def test_reviewer_agent_lifecycle():
    agent = SpecializedReviewerAgent()
    assert agent.role == AgentRole.REVIEWER
    assert any(c.name == "quality_assurance" for c in agent.capabilities)

    workspace = SharedWorkspace()
    workspace.set("research_summary", "Research content.")
    workspace.set("final_report", "Final report text.")

    memory = CollaborationMemory()
    task = TaskAssignment(title="Audit Quality", description="Audit outputs", target_role=AgentRole.REVIEWER)

    output = agent.execute_task(task, {}, workspace, memory)
    assert output.status == "completed"
    assert output.result["verification_passed"] is True
    assert workspace.has("review_result")
