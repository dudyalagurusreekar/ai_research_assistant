"""Multi-Agent Integration Bridge for Sprint 11 Browser Automation Platform."""

import logging
from typing import Any, Dict, Optional
from core.collaboration import MultiAgentCollaborationEngine
from tools.browser.platform.engine import BrowserPlatformEngine

logger = logging.getLogger("Tools.Browser.Integration.AgentIntegration")


class AgentBrowserBridge:
    """Enables multi-agent framework to share browser context sessions and distribute web sub-tasks."""

    def __init__(
        self,
        collaboration_engine: Optional[MultiAgentCollaborationEngine] = None,
        platform_engine: Optional[BrowserPlatformEngine] = None,
    ) -> None:
        self.collaboration_engine = collaboration_engine
        self.platform_engine = platform_engine or BrowserPlatformEngine()

    async def execute_agent_browser_subtask(self, agent_id: str, subtask_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a browser subtask on behalf of a specific agent."""
        logger.info(f"Agent '{agent_id}' requested browser subtask: {subtask_spec.get('action')}")
        action_name = subtask_spec.get("action", "navigate")
        url = subtask_spec.get("url", "https://example.com")

        if action_name == "navigate":
            res = await self.platform_engine.navigate(url)
        else:
            text = await self.platform_engine.extract_text()
            res = {"success": True, "text": text}

        return {
            "agent_id": agent_id,
            "status": "completed" if (getattr(res, "success", True) if not isinstance(res, dict) else res.get("success", True)) else "failed",
            "result": res.to_dict() if hasattr(res, "to_dict") else str(res),
        }
