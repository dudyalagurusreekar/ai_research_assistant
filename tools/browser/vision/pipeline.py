"""Vision Pipeline — Orchestrates capture, annotation, and visual verification.

Provides the high-level facade for integrating visual perception capabilities
into the browser agent. Coordinates ScreenshotManager, DOMAnnotator, and
VisualDiffer into a unified pipeline.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from tools.browser.core.browser import Browser
from tools.browser.vision.annotator import DOMAnnotator
from tools.browser.vision.capture import ScreenshotManager
from tools.browser.vision.differ import VisualDiffer
from tools.browser.vision.models import (
    ScreenshotCapture,
    VisualElement,
    VisualVerification,
    VisionConfig,
)

logger = logging.getLogger("VisionPipeline")


class VisionPipeline:
    """Orchestrates the full visual perception workflow for the browser agent.

    The VisionPipeline is the single entry point for all vision capabilities.
    It coordinates three sub-components:

    1. **ScreenshotManager** — Captures viewport, full-page, and element screenshots
    2. **DOMAnnotator** — Extracts interactive elements and draws bounding box overlays
    3. **VisualDiffer** — Compares before/after screenshots for action verification

    Architecture position:
        - Sits alongside BrowserActionExecutor in the execution layer
        - Receives the Browser instance for screenshot and DOM access
        - Provides visual state to the BrowserPlanner for grounded reasoning
        - Enables action outcome verification independent of DOM changes

    Example usage::

        config = VisionConfig(annotation_mode=AnnotationMode.FULL)
        pipeline = VisionPipeline(browser, config=config)

        # Get annotated view of current page
        capture, elements = pipeline.capture_and_annotate()

        # Verify an action had visual effect
        verification = pipeline.verify_action("click", before_capture, after_capture)

    Attributes:
        browser: Browser instance.
        config: Vision pipeline configuration.
        capture_manager: Screenshot capture handler.
        annotator: DOM element extractor and annotator.
        differ: Visual diff comparison engine.
    """

    def __init__(
        self,
        browser: Browser,
        config: Optional[VisionConfig] = None,
    ) -> None:
        """Initialize the Vision Pipeline.

        Args:
            browser: Browser instance providing screenshot and JS capabilities.
            config: Vision pipeline configuration. Defaults to VisionConfig().
        """
        self.browser = browser
        self.config = config or VisionConfig()

        # Initialize sub-components
        self.capture_manager = ScreenshotManager(browser, self.config)
        self.annotator = DOMAnnotator(browser, self.config)
        self.differ = VisualDiffer(self.config)

        self._logger = logger
        self._last_capture: Optional[ScreenshotCapture] = None

    def capture_and_annotate(
        self, full_page: bool = False
    ) -> Tuple[ScreenshotCapture, List[VisualElement]]:
        """Capture a screenshot and annotate it with detected interactive elements.

        This is the primary method for getting a visual representation of the
        current page state. It:
        1. Captures a screenshot (viewport or full-page)
        2. Extracts interactive elements from the DOM
        3. Draws bounding box annotations on the screenshot
        4. Returns both the annotated image and the element list

        Args:
            full_page: If True, capture the full scrollable page.
                If False (default), capture only the visible viewport.

        Returns:
            Tuple of (annotated_screenshot, detected_elements).
        """
        # 1. Capture screenshot
        if full_page:
            capture = self.capture_manager.capture_full_page()
        else:
            capture = self.capture_manager.capture_viewport()

        # 2. Extract interactive elements from DOM
        elements = self.annotator.extract_elements()

        # 3. Annotate screenshot with element overlays
        annotated = self.annotator.annotate_screenshot(capture, elements)

        # Store for later diff comparison
        self._last_capture = capture

        self._logger.info(
            f"Vision capture complete: {len(elements)} elements detected, "
            f"image {annotated.width}x{annotated.height}"
        )

        return annotated, elements

    def capture_raw(self, full_page: bool = False) -> ScreenshotCapture:
        """Capture a raw (unannotated) screenshot.

        Args:
            full_page: If True, capture full scrollable page.

        Returns:
            ScreenshotCapture: Raw screenshot without annotations.
        """
        if full_page:
            capture = self.capture_manager.capture_full_page()
        else:
            capture = self.capture_manager.capture_viewport()

        self._last_capture = capture
        return capture

    def detect_elements(self) -> List[VisualElement]:
        """Extract interactive elements from the current page DOM.

        Returns:
            List[VisualElement]: Detected elements sorted by position.
        """
        return self.annotator.extract_elements()

    def verify_action(
        self,
        action_name: str,
        before: Optional[ScreenshotCapture] = None,
        after: Optional[ScreenshotCapture] = None,
    ) -> VisualVerification:
        """Verify whether a browser action caused a visual change.

        If ``before`` is not provided, uses the last captured screenshot.
        If ``after`` is not provided, captures a new screenshot.

        Args:
            action_name: Name of the action to verify.
            before: Screenshot from before the action. Falls back to last capture.
            after: Screenshot from after the action. Falls back to new capture.

        Returns:
            VisualVerification: Comparison result with change metrics.
        """
        before_capture = before or self._last_capture
        if before_capture is None:
            self._logger.warning(
                "No 'before' screenshot available for verification. "
                "Capturing current state as 'after' only."
            )
            before_capture = ScreenshotCapture()

        after_capture = after or self.capture_manager.capture_viewport()

        verification = self.differ.compare(before_capture, after_capture, action_name)

        # Update last capture to the after image
        self._last_capture = after_capture

        return verification

    def capture_before_action(self) -> ScreenshotCapture:
        """Capture a screenshot to be used as the 'before' reference for verification.

        Call this immediately before executing an action, then call
        ``verify_action()`` after execution to compare.

        Returns:
            ScreenshotCapture: The captured 'before' screenshot.
        """
        capture = self.capture_manager.capture_viewport()
        self._last_capture = capture
        return capture

    def get_visual_state_summary(self) -> Dict[str, Any]:
        """Get a structured summary of the current visual page state.

        Combines element detection with page metadata for planner consumption.

        Returns:
            Dict[str, Any]: Visual state summary including elements and page info.
        """
        elements = self.annotator.extract_elements()

        # Categorize elements by type
        type_counts: Dict[str, int] = {}
        for el in elements:
            type_name = el.element_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        # Get page info
        url_res = self.browser.get_current_url()
        title_res = self.browser.get_page_title()

        return {
            "page_url": url_res.data if url_res.success else "",
            "page_title": title_res.data if title_res.success else "",
            "total_interactive_elements": len(elements),
            "element_type_counts": type_counts,
            "visible_elements": len([e for e in elements if e.is_visible]),
            "enabled_elements": len([e for e in elements if e.is_enabled]),
            "elements": [e.to_dict() for e in elements[:20]],  # Top 20 for context
        }

    def get_element_at_position(
        self, x: float, y: float, elements: Optional[List[VisualElement]] = None
    ) -> Optional[VisualElement]:
        """Find the element at a specific screen position.

        Useful for resolving click coordinates to specific DOM elements.

        Args:
            x: X coordinate in CSS pixels.
            y: Y coordinate in CSS pixels.
            elements: Optional pre-extracted element list. Extracts new if None.

        Returns:
            Optional[VisualElement]: The smallest element containing the point,
                or None if no element is at that position.
        """
        if elements is None:
            elements = self.annotator.extract_elements()

        matching = []
        for el in elements:
            bbox = el.bbox
            if (
                bbox.x <= x <= bbox.x + bbox.width
                and bbox.y <= y <= bbox.y + bbox.height
            ):
                matching.append(el)

        if not matching:
            return None

        # Return the smallest (most specific) matching element
        matching.sort(key=lambda e: e.bbox.area)
        return matching[0]
