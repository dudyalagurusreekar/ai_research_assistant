"""Planner Integration Bridge for Sprint 11 Browser Automation Platform."""

import logging
from typing import Any, Dict, List, Optional
from tools.browser.platform.engine import BrowserPlatformEngine
from tools.browser.platform.models import ActionType, BrowserAction

logger = logging.getLogger("Tools.Browser.Integration.PlannerIntegration")


class PlannerBrowserBridge:
    """Translates high-level research plan sub-goals into executable BrowserAction sequences."""

    def __init__(self, platform_engine: Optional[BrowserPlatformEngine] = None) -> None:
        self.engine = platform_engine or BrowserPlatformEngine()

    async def convert_subgoal_to_actions(self, subgoal_description: str, target_url: str = "") -> List[BrowserAction]:
        """Synthesize browser actions from plan sub-goal prompt."""
        actions = []
        desc_lower = subgoal_description.lower()

        if "navigate" in desc_lower or "open" in desc_lower or target_url:
            actions.append(BrowserAction(action_type=ActionType.NAVIGATE, url=target_url or "https://example.com"))

        if "search" in desc_lower or "query" in desc_lower:
            actions.append(
                BrowserAction(
                    action_type=ActionType.TYPE,
                    target_selector="input[type='search'], input[name='q'], input[type='text']",
                    text=subgoal_description,
                )
            )
            actions.append(BrowserAction(action_type=ActionType.PRESS_KEY, key_name="Enter"))

        if "extract" in desc_lower or "scrape" in desc_lower or "read" in desc_lower:
            actions.append(BrowserAction(action_type=ActionType.EXTRACT_TEXT))

        logger.info(f"Converted sub-goal '{subgoal_description}' into {len(actions)} browser action(s).")
        return actions
