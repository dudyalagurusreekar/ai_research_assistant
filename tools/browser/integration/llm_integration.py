"""LLM Orchestrator Integration Bridge for Sprint 11 Browser Automation Platform."""

import json
import logging
from typing import Any, Dict, Optional
from tools.browser.platform.dom_engine import DOMUnderstandingEngine
from tools.browser.platform.engine import BrowserPlatformEngine
from tools.browser.platform.models import ActionType, BrowserAction, DOMTree

logger = logging.getLogger("Tools.Browser.Integration.LLMIntegration")


class LLMBrowserBridge:
    """Formats DOM tree perceptions for LLM context prompts and parses structured LLM action outputs."""

    def __init__(self, platform_engine: Optional[BrowserPlatformEngine] = None) -> None:
        self.engine = platform_engine or BrowserPlatformEngine()
        self.dom_engine = DOMUnderstandingEngine()

    def build_llm_perception_prompt(self, dom_tree: DOMTree, goal: str = "") -> str:
        """Construct LLM perception prompt containing simplified DOM, interactive element list, and goal."""
        formatted_elements = self.dom_engine.format_interactive_elements_for_llm(dom_tree)
        prompt_lines = [
            f"=== ARA BROWSER PERCEPTION ===",
            f"Active Page: {dom_tree.title} ({dom_tree.url})",
            f"Research Goal: {goal}" if goal else "",
            "",
            formatted_elements,
            "",
            "Simplified DOM HTML:",
            dom_tree.simplified_html[:2000],
            "",
            "Respond with a JSON object specifying the next action:",
            '{"action_type": "click|type|navigate|extract_text", "target_selector": "...", "text": "...", "url": "..."}',
        ]
        return "\n".join(filter(None, prompt_lines))

    def parse_llm_action(self, llm_response: str) -> BrowserAction:
        """Parse structured JSON from LLM response into strongly typed BrowserAction."""
        try:
            # Extract JSON block if surrounded by markdown code blocks
            clean_res = llm_response.strip()
            if "```json" in clean_res:
                clean_res = clean_res.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_res:
                clean_res = clean_res.split("```")[1].split("```")[0].strip()

            data = json.loads(clean_res)
            act_str = data.get("action_type", "navigate").lower()

            action_type = ActionType.NAVIGATE
            if act_str == "click":
                action_type = ActionType.CLICK
            elif act_str == "type":
                action_type = ActionType.TYPE
            elif act_str in {"extract", "extract_text"}:
                action_type = ActionType.EXTRACT_TEXT
            elif act_str == "screenshot":
                action_type = ActionType.SCREENSHOT

            return BrowserAction(
                action_type=action_type,
                target_selector=data.get("target_selector"),
                url=data.get("url"),
                text=data.get("text"),
                value=data.get("value"),
            )
        except Exception as e:
            logger.warning(f"Could not parse LLM action response ({e}). Defaulting to navigate action.")
            return BrowserAction(action_type=ActionType.NAVIGATE, url="https://example.com")
