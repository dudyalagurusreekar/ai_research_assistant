"""Screenshot Capture Manager.

Handles full-page, viewport, and element-specific screenshot capture
via the Browser facade and Playwright engine. Manages image encoding,
storage, and metadata enrichment.
"""

import io
import logging
import os
import time
from typing import Optional

from tools.browser.core.browser import Browser
from tools.browser.vision.models import ScreenshotCapture, VisionConfig

logger = logging.getLogger("ScreenshotManager")


class ScreenshotManager:
    """Captures and stores browser screenshots with metadata.

    Uses the Browser facade's execute_javascript and capture_screenshot
    capabilities to obtain viewport and full-page screenshots. Images
    are stored as PNG byte buffers with optional disk persistence.

    Attributes:
        browser: The Browser instance used for capturing.
        config: Vision pipeline configuration.
    """

    def __init__(self, browser: Browser, config: Optional[VisionConfig] = None) -> None:
        """Initialize the Screenshot Manager.

        Args:
            browser: Browser instance providing screenshot capabilities.
            config: Vision pipeline configuration. Defaults to VisionConfig().
        """
        self.browser = browser
        self.config = config or VisionConfig()
        self._logger = logger

        # Ensure capture directory exists
        if self.config.save_captures_to_disk:
            os.makedirs(os.path.abspath(self.config.capture_directory), exist_ok=True)

    def capture_viewport(self) -> ScreenshotCapture:
        """Capture a screenshot of the current browser viewport.

        Returns:
            ScreenshotCapture: The captured screenshot with metadata.
        """
        capture = ScreenshotCapture()

        try:
            # Get page metadata
            url_res = self.browser.get_current_url()
            capture.page_url = url_res.data if url_res.success else ""

            title_res = self.browser.get_page_title()
            capture.page_title = title_res.data if title_res.success else ""

            # Capture screenshot via browser
            screenshot_res = self.browser.capture_screenshot()
            if screenshot_res.success and screenshot_res.data:
                screenshot_data = screenshot_res.data
                if isinstance(screenshot_data, dict):
                    # The browser may return screenshot as a dict with path
                    file_path = screenshot_data.get("screenshot_path", "")
                    if file_path and os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            capture.image_bytes = f.read()
                        capture.file_path = file_path
                elif isinstance(screenshot_data, bytes):
                    capture.image_bytes = screenshot_data
                elif isinstance(screenshot_data, str) and os.path.exists(screenshot_data):
                    with open(screenshot_data, "rb") as f:
                        capture.image_bytes = f.read()
                    capture.file_path = screenshot_data

            # Get viewport dimensions
            dim_res = self.browser.execute_javascript(
                "JSON.stringify({width: window.innerWidth, height: window.innerHeight})"
            )
            if dim_res.success and dim_res.data:
                try:
                    import json
                    dims = json.loads(str(dim_res.data))
                    capture.width = dims.get("width", 0)
                    capture.height = dims.get("height", 0)
                except (ValueError, TypeError):
                    pass

            capture.is_full_page = False
            capture.timestamp = time.time()

            # Save to disk if configured and not already saved
            if self.config.save_captures_to_disk and not capture.file_path:
                capture.file_path = self._save_to_disk(capture)

            self._logger.debug(
                f"Viewport captured: {capture.width}x{capture.height} "
                f"({len(capture.image_bytes)} bytes)"
            )

        except Exception as e:
            self._logger.error(f"Viewport capture failed: {e}")

        return capture

    def capture_full_page(self) -> ScreenshotCapture:
        """Capture a full-page screenshot (scrolling capture).

        Falls back to viewport capture if full-page is not supported.

        Returns:
            ScreenshotCapture: The captured screenshot with metadata.
        """
        capture = self.capture_viewport()
        capture.is_full_page = True

        # Try to capture with full_page flag via JavaScript scroll dimensions
        try:
            dim_res = self.browser.execute_javascript(
                "JSON.stringify({width: document.documentElement.scrollWidth, "
                "height: document.documentElement.scrollHeight})"
            )
            if dim_res.success and dim_res.data:
                import json
                dims = json.loads(str(dim_res.data))
                capture.width = dims.get("width", capture.width)
                capture.height = dims.get("height", capture.height)
        except Exception:
            pass

        return capture

    def capture_element(self, selector: str) -> ScreenshotCapture:
        """Capture a screenshot of a specific DOM element.

        Falls back to a viewport capture if the element cannot be
        isolated. Uses JavaScript to get element bounding rect and
        crops from a viewport capture.

        Args:
            selector: CSS selector targeting the element to capture.

        Returns:
            ScreenshotCapture: The captured element screenshot.
        """
        capture = self.capture_viewport()

        try:
            # Get element bounding rect
            rect_js = (
                f"(() => {{"
                f"  const el = document.querySelector('{selector}');"
                f"  if (!el) return null;"
                f"  const r = el.getBoundingClientRect();"
                f"  return JSON.stringify({{x: r.x, y: r.y, width: r.width, height: r.height}});"
                f"}})()"
            )
            rect_res = self.browser.execute_javascript(rect_js)

            if rect_res.success and rect_res.data:
                import json
                rect = json.loads(str(rect_res.data))

                # Crop the image if we have Pillow and valid bytes
                if capture.image_bytes and rect:
                    try:
                        from PIL import Image

                        img = Image.open(io.BytesIO(capture.image_bytes))
                        x = max(0, int(rect["x"]))
                        y = max(0, int(rect["y"]))
                        w = int(rect["width"])
                        h = int(rect["height"])

                        if w > 0 and h > 0:
                            cropped = img.crop((x, y, x + w, y + h))
                            buf = io.BytesIO()
                            cropped.save(buf, format="PNG")
                            capture.image_bytes = buf.getvalue()
                            capture.width = w
                            capture.height = h
                    except ImportError:
                        self._logger.warning("Pillow not available for element cropping")
                    except Exception as e:
                        self._logger.warning(f"Element crop failed: {e}")

        except Exception as e:
            self._logger.error(f"Element capture failed for '{selector}': {e}")

        return capture

    def _save_to_disk(self, capture: ScreenshotCapture) -> str:
        """Save a screenshot capture to the filesystem.

        Args:
            capture: ScreenshotCapture with image_bytes to save.

        Returns:
            str: Absolute path to the saved file.
        """
        if not capture.image_bytes:
            return ""

        directory = os.path.abspath(self.config.capture_directory)
        os.makedirs(directory, exist_ok=True)

        filename = f"{capture.capture_id}_{int(capture.timestamp)}.png"
        filepath = os.path.join(directory, filename)

        try:
            with open(filepath, "wb") as f:
                f.write(capture.image_bytes)
            self._logger.debug(f"Screenshot saved: {filepath}")
            return filepath
        except IOError as e:
            self._logger.error(f"Failed to save screenshot: {e}")
            return ""
