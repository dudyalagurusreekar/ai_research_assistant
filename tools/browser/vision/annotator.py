"""DOM Annotator — Visual element detection and screenshot annotation.

Extracts interactive element positions from the DOM via JavaScript,
classifies them into visual element types, and draws bounding box
overlays on screenshots using Pillow.
"""

import io
import json
import logging
from typing import Dict, List, Optional, Tuple

from tools.browser.core.browser import Browser
from tools.browser.vision.models import (
    AnnotationMode,
    BoundingBox,
    ElementType,
    ScreenshotCapture,
    VisualElement,
    VisionConfig,
)

logger = logging.getLogger("DOMAnnotator")

# JavaScript that extracts bounding rectangles and metadata for all
# interactive elements on the page. Returns a JSON array.
_EXTRACT_ELEMENTS_JS = """
(() => {
    const SELECTORS = [
        'a[href]', 'button', 'input', 'select', 'textarea',
        '[role="button"]', '[role="link"]', '[role="checkbox"]',
        '[role="tab"]', '[role="menuitem"]', '[onclick]',
        'label', 'summary', '[contenteditable="true"]'
    ];

    const seen = new Set();
    const results = [];

    for (const sel of SELECTORS) {
        for (const el of document.querySelectorAll(sel)) {
            if (seen.has(el)) continue;
            seen.add(el);

            const rect = el.getBoundingClientRect();
            if (rect.width <= 0 || rect.height <= 0) continue;

            const isVisible = (
                rect.top < window.innerHeight &&
                rect.bottom > 0 &&
                rect.left < window.innerWidth &&
                rect.right > 0 &&
                getComputedStyle(el).visibility !== 'hidden' &&
                getComputedStyle(el).display !== 'none'
            );

            const tag = el.tagName.toLowerCase();
            const type = el.getAttribute('type') || '';
            const role = el.getAttribute('role') || '';
            const text = (el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim().substring(0, 80);

            let elementType = 'UNKNOWN';
            if (tag === 'button' || role === 'button' || type === 'submit' || type === 'button') {
                elementType = 'BUTTON';
            } else if (tag === 'a') {
                elementType = 'LINK';
            } else if (tag === 'input' && (type === 'checkbox' || type === 'radio')) {
                elementType = 'CHECKBOX';
            } else if (tag === 'input' || tag === 'textarea') {
                elementType = 'INPUT';
            } else if (tag === 'select') {
                elementType = 'SELECT';
            } else if (tag === 'img') {
                elementType = 'IMAGE';
            } else {
                elementType = 'INTERACTIVE';
            }

            // Build a reasonable CSS selector
            let selector = tag;
            if (el.id) {
                selector = '#' + CSS.escape(el.id);
            } else if (el.className && typeof el.className === 'string') {
                const cls = el.className.trim().split(/\\s+/).slice(0, 2).map(c => '.' + CSS.escape(c)).join('');
                selector = tag + cls;
            }

            results.push({
                tag: tag,
                type: elementType,
                bbox: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
                label: text,
                selector: selector,
                is_visible: isVisible,
                is_enabled: !el.disabled,
                attributes: {
                    id: el.id || '',
                    name: el.getAttribute('name') || '',
                    href: el.getAttribute('href') || '',
                    type: type,
                    role: role,
                }
            });
        }
    }

    return JSON.stringify(results);
})()
"""


# Color palette for different element types
_TYPE_COLORS: Dict[ElementType, Tuple[int, int, int]] = {
    ElementType.BUTTON: (0, 150, 255),    # Blue
    ElementType.LINK: (0, 200, 100),      # Green
    ElementType.INPUT: (255, 165, 0),     # Orange
    ElementType.SELECT: (148, 0, 211),    # Purple
    ElementType.CHECKBOX: (255, 20, 147), # Pink
    ElementType.IMAGE: (128, 128, 128),   # Gray
    ElementType.TEXT: (100, 100, 100),     # Dark gray
    ElementType.INTERACTIVE: (255, 215, 0), # Gold
    ElementType.UNKNOWN: (255, 0, 0),     # Red
}


class DOMAnnotator:
    """Extracts interactive elements from the DOM and annotates screenshots.

    Combines JavaScript-based element detection with Pillow-based image
    annotation to produce visually grounded representations of web pages.

    Architecture position:
        - Receives raw screenshots from ScreenshotManager
        - Uses Browser.execute_javascript for DOM element extraction
        - Outputs annotated ScreenshotCapture + VisualElement lists
        - Fed to VisionPipeline for integration with the planner

    Attributes:
        browser: Browser instance for DOM queries.
        config: Vision pipeline configuration.
    """

    def __init__(self, browser: Browser, config: Optional[VisionConfig] = None) -> None:
        """Initialize the DOM Annotator.

        Args:
            browser: Browser instance for JavaScript execution.
            config: Vision configuration. Defaults to VisionConfig().
        """
        self.browser = browser
        self.config = config or VisionConfig()
        self._logger = logger

    def extract_elements(self) -> List[VisualElement]:
        """Extract interactive elements from the current page DOM.

        Runs JavaScript on the page to detect all interactive elements,
        their positions, types, and metadata.

        Returns:
            List[VisualElement]: Detected elements sorted by position (top to bottom).
        """
        elements: List[VisualElement] = []

        try:
            res = self.browser.execute_javascript(_EXTRACT_ELEMENTS_JS)
            if not res.success or not res.data:
                self._logger.warning("Element extraction JavaScript returned no data.")
                return elements

            raw_data = str(res.data)
            items = json.loads(raw_data)

            for idx, item in enumerate(items):
                if idx >= self.config.max_elements_to_annotate:
                    break

                try:
                    element_type = ElementType(item.get("type", "UNKNOWN"))
                except ValueError:
                    element_type = ElementType.UNKNOWN

                bbox_data = item.get("bbox", {})
                bbox = BoundingBox(
                    x=bbox_data.get("x", 0),
                    y=bbox_data.get("y", 0),
                    width=bbox_data.get("width", 0),
                    height=bbox_data.get("height", 0),
                )

                element = VisualElement(
                    element_type=element_type,
                    bbox=bbox,
                    label=item.get("label", ""),
                    selector=item.get("selector", ""),
                    is_visible=item.get("is_visible", True),
                    is_enabled=item.get("is_enabled", True),
                    attributes=item.get("attributes", {}),
                )
                elements.append(element)

        except json.JSONDecodeError as e:
            self._logger.error(f"Failed to parse element extraction JSON: {e}")
        except Exception as e:
            self._logger.error(f"Element extraction failed: {e}")

        # Sort by vertical position (top to bottom), then left to right
        elements.sort(key=lambda el: (el.bbox.y, el.bbox.x))

        self._logger.debug(f"Extracted {len(elements)} interactive elements.")
        return elements

    def annotate_screenshot(
        self,
        capture: ScreenshotCapture,
        elements: List[VisualElement],
    ) -> ScreenshotCapture:
        """Draw element annotations onto a screenshot image.

        Renders bounding boxes and/or labels over detected elements using
        Pillow. The original capture is not modified; a new ScreenshotCapture
        is returned with the annotated image bytes.

        Args:
            capture: The raw screenshot to annotate.
            elements: List of detected visual elements to draw.

        Returns:
            ScreenshotCapture: New capture with annotated image bytes.
        """
        if self.config.annotation_mode == AnnotationMode.NONE:
            return capture

        if not capture.image_bytes:
            self._logger.warning("Cannot annotate: screenshot has no image data.")
            return capture

        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            self._logger.warning("Pillow not available — skipping annotation.")
            return capture

        try:
            img = Image.open(io.BytesIO(capture.image_bytes))
            draw = ImageDraw.Draw(img)

            # Try to use a monospace font, fall back to default
            try:
                font = ImageFont.truetype("arial.ttf", self.config.label_font_size)
            except (IOError, OSError):
                font = ImageFont.load_default()

            for idx, element in enumerate(elements):
                if not element.is_visible:
                    continue

                bbox = element.bbox
                color = _TYPE_COLORS.get(element.element_type, self.config.box_color_rgb)

                # Draw bounding box
                if self.config.annotation_mode in (AnnotationMode.BOUNDING_BOX, AnnotationMode.FULL):
                    draw.rectangle(
                        [bbox.x, bbox.y, bbox.x + bbox.width, bbox.y + bbox.height],
                        outline=color,
                        width=2,
                    )

                # Draw label
                if self.config.annotation_mode in (AnnotationMode.LABEL_ONLY, AnnotationMode.FULL):
                    label_text = f"[{idx}] {element.element_type.value}"
                    if element.label:
                        label_text += f": {element.label[:30]}"

                    # Background rectangle for readability
                    text_bbox = draw.textbbox((0, 0), label_text, font=font)
                    text_w = text_bbox[2] - text_bbox[0]
                    text_h = text_bbox[3] - text_bbox[1]

                    label_x = bbox.x
                    label_y = max(0, bbox.y - text_h - 4)

                    draw.rectangle(
                        [label_x, label_y, label_x + text_w + 4, label_y + text_h + 2],
                        fill=(0, 0, 0, 180),
                    )
                    draw.text(
                        (label_x + 2, label_y + 1),
                        label_text,
                        fill=(255, 255, 255),
                        font=font,
                    )

            # Export annotated image
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            annotated_bytes = buf.getvalue()

            annotated_capture = ScreenshotCapture(
                image_bytes=annotated_bytes,
                width=capture.width,
                height=capture.height,
                page_url=capture.page_url,
                page_title=capture.page_title,
                timestamp=capture.timestamp,
                is_full_page=capture.is_full_page,
            )

            self._logger.debug(
                f"Annotated screenshot with {len([e for e in elements if e.is_visible])} elements."
            )
            return annotated_capture

        except Exception as e:
            self._logger.error(f"Screenshot annotation failed: {e}")
            return capture
