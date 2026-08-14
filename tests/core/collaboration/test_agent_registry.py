"""Unit tests for AgentRegistry lifecycle management and capability resolution."""

import pytest

from core.collaboration.agents import SpecializedDataAgent, SpecializedResearchAgent
from core.collaboration.components.registry import AgentRegistry
from core.collaboration.models.agent_info import AgentMetadata, AgentRole, AgentStatus


def test_agent_registration_and_lookup():
    registry = AgentRegistry()
    registry.clear()

    agent = SpecializedResearchAgent(agent_id="res_001")
    meta = registry.register_agent(agent)

    assert meta.agent_id == "res_001"
    assert registry.get_agent("res_001") is agent
    assert registry.get_metadata("res_001").role == AgentRole.RESEARCH

    agents_list = registry.list_agents(role=AgentRole.RESEARCH)
    assert len(agents_list) == 1
    assert agents_list[0].agent_id == "res_001"


def test_find_best_agent_by_capability():
    registry = AgentRegistry()
    registry.clear()

    res_agent = SpecializedResearchAgent(agent_id="res_001")
    data_agent = SpecializedDataAgent(agent_id="data_001")

    registry.register_agent(res_agent)
    registry.register_agent(data_agent)

    found_res = registry.find_best_agent(AgentRole.RESEARCH, required_capabilities=["web_search"])
    assert found_res is res_agent

    found_data = registry.find_best_agent(AgentRole.DATA, required_capabilities=["data_profiling"])
    assert found_data is data_agent


def test_agent_unregistration_and_status_update():
    registry = AgentRegistry()
    registry.clear()

    agent = SpecializedResearchAgent(agent_id="res_002")
    registry.register_agent(agent)

    registry.update_status("res_002", AgentStatus.BUSY)
    assert registry.get_metadata("res_002").status == AgentStatus.BUSY

    assert registry.unregister_agent("res_002") is True
    assert registry.get_agent("res_002") is None
