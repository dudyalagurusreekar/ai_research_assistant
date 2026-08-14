"""Tool Selection Integration Bridge for Sprint 11 Browser Automation Platform."""

import logging
from typing import Any, Dict, Optional
from tools.browser.platform.engine import BrowserPlatformEngine

logger = logging.getLogger("Tools.Browser.Integration.ToolSelectionIntegration")


class ToolSelectionBrowserBridge:
    """Connects Browser Automation Platform to Adaptive Tool Selection / Capability Router."""

    def __init__(
        self,
        router: Optional[Any] = None,
        platform_engine: Optional[BrowserPlatformEngine] = None,
    ) -> None:
        self.router = router
        self.engine = platform_engine or BrowserPlatformEngine()

    def register_capabilities(self) -> None:
        """Register browser platform capability signatures into router."""
        capabilities = [
            "browser_navigate",
            "browser_click",
            "browser_type",
            "browser_extract_text",
            "browser_extract_table",
            "browser_screenshot",
            "browser_workflow_execute",
        ]
        if self.router and hasattr(self.router, "register_capability"):
            for cap in capabilities:
                self.router.register_capability(cap, handler=self._handle_capability)
            logger.info(f"Registered {len(capabilities)} browser capabilities into CapabilityRouter.")

    async def _handle_capability(self, capability: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch router calls directly to BrowserPlatformEngine."""
        action = parameters.get("action") or capability.replace("browser_", "")
        url = parameters.get("url", "")
        res = await self.engine.navigate(url) if action == "navigate" else await self.engine.extract_text()
        return {"success": res.success, "message": res.message, "url": res.url, "data": res.data}
