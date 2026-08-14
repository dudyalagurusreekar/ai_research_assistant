"""Integration tests for Sprint 11 Browser Automation Platform and Subsystem Bridges."""

import pytest
import asyncio
from tools.browser.platform.engine import BrowserPlatformEngine
from tools.browser.platform.models import ActionResult, ActionType, DOMTree
from tools.browser.integration.planner_integration import PlannerBrowserBridge
from tools.browser.integration.tool_selection_integration import ToolSelectionBrowserBridge
from tools.browser.integration.llm_integration import LLMBrowserBridge
from tools.browser.integration.reflection_integration import ReflectionBrowserBridge
from tools.browser.integration.learning_integration import LearningBrowserBridge
from tools.browser.integration.agent_integration import AgentBrowserBridge
from tools.browser.integration.workflow_integration import WorkflowBrowserBridge


def test_planner_browser_bridge():
    async def _test():
        bridge = PlannerBrowserBridge()
        actions = await bridge.convert_subgoal_to_actions("Navigate to website and search for quantum computing", target_url="https://example.com")
        
        assert len(actions) >= 2
        assert actions[0].action_type == ActionType.NAVIGATE
        assert actions[0].url == "https://example.com"

    asyncio.run(_test())


def test_tool_selection_browser_bridge():
    bridge = ToolSelectionBrowserBridge()
    bridge.register_capabilities()


def test_llm_browser_bridge():
    bridge = LLMBrowserBridge()
    dom_tree = DOMTree(
        url="https://example.com",
        title="Example Page",
        nodes=[],
        interactive_elements=[],
        simplified_html="<html><body><h1>Test</h1></body></html>",
    )
    
    prompt = bridge.build_llm_perception_prompt(dom_tree, goal="Find documentation")
    assert "Example Page" in prompt
    assert "Find documentation" in prompt
    
    # Test JSON action parsing
    llm_json = '```json\n{"action_type": "type", "target_selector": "#search", "text": "AI models"}\n```'
    parsed_action = bridge.parse_llm_action(llm_json)
    assert parsed_action.action_type == ActionType.TYPE
    assert parsed_action.target_selector == "#search"
    assert parsed_action.text == "AI models"


def test_reflection_browser_bridge():
    bridge = ReflectionBrowserBridge()
    res_ok = ActionResult(success=True, action_type=ActionType.NAVIGATE, url="https://example.com/page1")
    
    eval_ok = bridge.evaluate_browser_step(res_ok)
    assert eval_ok["success"] is True
    assert eval_ok["is_stasis_loop"] is False
    
    # Simulate stasis loop (same URL repeated 4 times)
    for _ in range(3):
        bridge.evaluate_browser_step(res_ok)
        
    eval_loop = bridge.evaluate_browser_step(res_ok)
    assert eval_loop["is_stasis_loop"] is True
    assert eval_loop["recommendation"] == "retry_with_text_fallback"


def test_learning_browser_bridge():
    bridge = LearningBrowserBridge()
    res = ActionResult(success=True, action_type=ActionType.NAVIGATE, execution_time_ms=120.0)
    
    bridge.record_experience("example.com", "navigate", res)


def test_agent_browser_bridge():
    async def _test():
        bridge = AgentBrowserBridge()
        subtask = {"action": "navigate", "url": "https://example.com"}
        
        agent_res = await bridge.execute_agent_browser_subtask("ResearchAgent_1", subtask)
        assert agent_res["agent_id"] == "ResearchAgent_1"
        assert agent_res["status"] == "completed"

    asyncio.run(_test())


def test_workflow_browser_bridge():
    async def _test():
        bridge = WorkflowBrowserBridge()
        step_data = {"url": "https://example.com"}
        
        wf_res = await bridge.execute_workflow_research_step(step_data)
        assert wf_res["success"] is True
        assert wf_res["url"].startswith("https://example.com")

    asyncio.run(_test())
