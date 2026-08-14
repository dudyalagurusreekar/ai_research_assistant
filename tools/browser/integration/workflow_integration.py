"""Autonomous Research Workflow Integration Bridge for Sprint 11 Browser Automation Platform."""

import logging
from typing import Any, Dict, Optional
from core.workflow import AutonomousResearchEngine
from tools.browser.platform.engine import BrowserPlatformEngine
from tools.browser.platform.models import ActionType, BrowserAction

logger = logging.getLogger("Tools.Browser.Integration.WorkflowIntegration")


class WorkflowBrowserBridge:
    """Hooks Browser Automation Platform directly into AutonomousResearchEngine step execution loop."""

    def __init__(
        self,
        workflow_engine: Optional[AutonomousResearchEngine] = None,
        platform_engine: Optional[BrowserPlatformEngine] = None,
    ) -> None:
        self.workflow_engine = workflow_engine
        self.platform_engine = platform_engine or BrowserPlatformEngine()

    async def execute_workflow_research_step(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a browser step within the main Autonomous Research Workflow loop."""
        url = step_data.get("url") or step_data.get("target") or "https://example.com"
        logger.info(f"Executing workflow research browser step for target URL '{url}'.")

        nav_res = await self.platform_engine.navigate(url)
        if not nav_res.success:
            return {"success": False, "error": nav_res.error or nav_res.message}

        extracted_text = await self.platform_engine.extract_text()
        screenshot_res = await self.platform_engine.capture_screenshot()

        return {
            "success": True,
            "url": nav_res.url,
            "content_summary": extracted_text[:1000],
            "screenshot_path": screenshot_res.screenshot_path,
            "latency_ms": nav_res.execution_time_ms,
        }
