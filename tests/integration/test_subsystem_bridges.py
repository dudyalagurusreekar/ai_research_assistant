"""Integration tests for all 10 Subsystem Bridges."""

import pytest
import asyncio

from tools.integration.bridges.planner_bridge import PlannerConnectorBridge
from tools.integration.bridges.tool_selection_bridge import ToolSelectionConnectorBridge
from tools.integration.bridges.llm_bridge import LLMConnectorBridge
from tools.integration.bridges.reflection_bridge import ReflectionConnectorBridge
from tools.integration.bridges.learning_bridge import LearningConnectorBridge
from tools.integration.bridges.data_intelligence_bridge import DataIntelligenceConnectorBridge
from tools.integration.bridges.agent_bridge import AgentConnectorBridge
from tools.integration.bridges.knowledge_graph_bridge import KnowledgeGraphConnectorBridge
from tools.integration.bridges.browser_bridge import BrowserConnectorBridge
from tools.integration.bridges.workflow_bridge import WorkflowConnectorBridge


def test_planner_bridge():
    bridge = PlannerConnectorBridge()
    steps = bridge.get_connector_plan_steps("gmail", "Fetch latest email reports")
    assert len(steps) == 3
    assert steps[0]["tool"] == "integration_tool"


def test_tool_selection_bridge():
    bridge = ToolSelectionConnectorBridge()
    tools = bridge.register_connector_tools()
    assert len(tools) == 9
    tool_names = [t["name"] for t in tools]
    assert "gmail_tool" in tool_names
    assert "github_tool" in tool_names
    assert "jira_tool" in tool_names


def test_llm_bridge():
    bridge = LLMConnectorBridge()
    schemas = bridge.get_function_schemas()
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "execute_universal_connector"


def test_reflection_bridge():
    bridge = ReflectionConnectorBridge()
    refl_ok = bridge.reflect_on_execution({"success": True, "status_code": 200})
    assert refl_ok["assessment"] == "OPTIMAL"

    refl_rate = bridge.reflect_on_execution({"success": False, "status_code": 429})
    assert refl_rate["assessment"] == "RATE_LIMITED"


def test_learning_bridge():
    bridge = LearningConnectorBridge()
    bridge.record_experience("gmail", "search", latency_ms=45.0, success=True)
    recs = bridge.get_connector_recommendations("code research")
    assert "preferred_connector" in recs


def test_data_intelligence_bridge():
    bridge = DataIntelligenceConnectorBridge()
    res = bridge.process_retrieved_data("database", [{"id": 1, "val": "A"}, {"id": 2, "val": "B"}])
    assert res["profile"]["num_records"] == 2
    assert "id" in res["profile"]["columns"]


def test_agent_bridge():
    bridge = AgentConnectorBridge()
    bridge.authorize_agent_session("agent_researcher", ["gmail", "github"])
    assert bridge.can_agent_access("agent_researcher", "gmail") is True
    assert bridge.can_agent_access("agent_researcher", "slack") is False


def test_knowledge_graph_bridge():
    bridge = KnowledgeGraphConnectorBridge()
    res = bridge.ingest_entity("jira", "issue", {"id": "101", "summary": "Fix Bug"})
    assert res["node"]["node_id"] == "kg_jira_101"
    summary = bridge.get_graph_summary()
    assert summary["nodes_count"] == 1


def test_browser_bridge():
    async def _test():
        bridge = BrowserConnectorBridge()
        auth_res = await bridge.execute_visual_auth_flow("slack", "https://slack.com/oauth")
        assert auth_res["status"] == "completed"

    asyncio.run(_test())


def test_workflow_bridge():
    bridge = WorkflowConnectorBridge()
    res = bridge.execute_workflow_connector_phase("wf_001", "github", "Search repositories")
    assert res["status"] == "completed"
