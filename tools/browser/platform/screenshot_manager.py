"""Screenshot Manager for Sprint 11 Browser Automation Platform."""

import base64
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional
from tools.browser.platform.models import ActionResult, ActionType

logger = logging.getLogger("Tools.Browser.Platform.ScreenshotManager")


class ScreenshotManager:
    """Captures viewport, full-page, and element screenshots with base64 encoding."""

    def __init__(self, output_dir: Optional[str] = None) -> None:
        self.output_dir = Path(output_dir or ".browser_artifacts/screenshots")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def capture_screenshot(
        self,
        page: Any,
        full_page: bool = False,
        selector: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> ActionResult:
        """Capture screenshot and save to file + return base64 string."""
        start_time = time.time()
        url = getattr(page, "url", "about:blank")
        fname = filename or f"screenshot_{int(time.time() * 1000)}.png"
        filepath = self.output_dir / fname

        image_bytes: bytes = b""
        b64_str = ""

        try:
            if hasattr(page, "screenshot"):
                if selector and hasattr(page, "locator"):
                    locator = page.locator(selector)
                    image_bytes = await locator.screenshot(type="png")
                else:
                    image_bytes = await page.screenshot(full_page=full_page, type="png")

                with open(filepath, "wb") as f:
                    f.write(image_bytes)
                b64_str = base64.b64encode(image_bytes).decode("utf-8")
            else:
                # Mock screenshot
                b64_str = base64.b64encode(b"Mock Screenshot Content").decode("utf-8")
                with open(filepath, "wb") as f:
                    f.write(b"Mock Screenshot Content")

            return ActionResult(
                success=True,
                action_type=ActionType.SCREENSHOT,
                message=f"Captured screenshot saved to '{filepath}'.",
                url=url,
                screenshot_path=str(filepath),
                data={
                    "screenshot_path": str(filepath),
                    "base64_image": b64_str,
                    "full_page": full_page,
                    "selector": selector,
                },
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return ActionResult(
                success=False,
                action_type=ActionType.SCREENSHOT,
                message=f"Screenshot capture failed: {e}",
                url=url,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )
