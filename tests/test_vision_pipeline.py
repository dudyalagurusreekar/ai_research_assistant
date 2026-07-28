"""Comprehensive tests for the Vision Pipeline component.

Tests screenshot capture, DOM annotation, visual diffing, pipeline
orchestration, and edge cases.
"""

import io
import os
import json
import shutil
import pytest
from unittest.mock import MagicMock

from tools.browser.vision.models import (
    AnnotationMode,
    BoundingBox,
    ElementType,
    ScreenshotCapture,
    VisualElement,
    VisualVerification,
    VisionConfig,
)
from tools.browser.vision.capture import ScreenshotManager
from tools.browser.vision.annotator import DOMAnnotator
from tools.browser.vision.differ import VisualDiffer
from tools.browser.vision.pipeline import VisionPipeline


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

TEST_CAPTURE_DIR = ".browser_artifacts/test_screenshots"


@pytest.fixture
def mock_browser():
    """Create a mock Browser instance with screenshot capabilities."""
    browser = MagicMock()
    browser.get_current_url.return_value = MagicMock(success=True, data="https://example.com")
    browser.get_page_title.return_value = MagicMock(success=True, data="Example Page")
    browser.get_page_html.return_value = MagicMock(success=True, data="<html></html>")
    browser.capture_screenshot.return_value = MagicMock(success=True, data=b"")
    browser.execute_javascript.return_value = MagicMock(success=True, data="[]")
    return browser


@pytest.fixture
def vision_config():
    """Create a test vision config."""
    return VisionConfig(
        capture_directory=TEST_CAPTURE_DIR,
        annotation_mode=AnnotationMode.FULL,
        diff_threshold=1.0,
        save_captures_to_disk=False,  # Don't save files in tests
    )


@pytest.fixture(autouse=True)
def cleanup_test_dir():
    """Cleanup test screenshot directory after each test."""
    yield
    if os.path.exists(TEST_CAPTURE_DIR):
        shutil.rmtree(TEST_CAPTURE_DIR, ignore_errors=True)


# ─────────────────────────────────────────────
# Vision Models Tests
# ─────────────────────────────────────────────

class TestVisionModels:
    """Tests for vision data models."""

    def test_bounding_box_center(self):
        """BoundingBox center should be calculated correctly."""
        bbox = BoundingBox(x=100, y=200, width=50, height=30)
        assert bbox.center == (125.0, 215.0)

    def test_bounding_box_area(self):
        """BoundingBox area should be width * height."""
        bbox = BoundingBox(x=0, y=0, width=100, height=50)
        assert bbox.area == 5000.0

    def test_bounding_box_serialization(self):
        """BoundingBox should serialize and deserialize correctly."""
        bbox = BoundingBox(x=10, y=20, width=30, height=40)
        d = bbox.to_dict()
        restored = BoundingBox.from_dict(d)
        assert restored.x == 10
        assert restored.y == 20
        assert restored.width == 30
        assert restored.height == 40

    def test_visual_element_defaults(self):
        """VisualElement should have sensible defaults."""
        elem = VisualElement()
        assert elem.element_type == ElementType.UNKNOWN
        assert elem.is_visible is True
        assert elem.is_enabled is True
        assert elem.confidence == 1.0

    def test_visual_element_serialization(self):
        """VisualElement should serialize to dictionary."""
        elem = VisualElement(
            element_type=ElementType.BUTTON,
            bbox=BoundingBox(x=10, y=20, width=80, height=30),
            label="Submit",
            selector="button.submit",
        )
        d = elem.to_dict()
        assert d["element_type"] == "BUTTON"
        assert d["label"] == "Submit"
        assert d["selector"] == "button.submit"
        assert d["bbox"]["width"] == 80

    def test_screenshot_capture_metadata(self):
        """ScreenshotCapture should store metadata correctly."""
        cap = ScreenshotCapture(
            image_bytes=b"fake_png_data",
            width=1920,
            height=1080,
            page_url="https://example.com",
        )
        d = cap.to_dict()
        assert d["width"] == 1920
        assert d["height"] == 1080
        assert d["size_bytes"] == 13  # len(b"fake_png_data")
        assert d["page_url"] == "https://example.com"

    def test_visual_verification_serialization(self):
        """VisualVerification should serialize correctly."""
        vv = VisualVerification(
            action_name="click",
            change_detected=True,
            change_percentage=15.5,
            change_description="Moderate change",
        )
        d = vv.to_dict()
        assert d["action_name"] == "click"
        assert d["change_detected"] is True
        assert d["change_percentage"] == 15.5

    def test_element_type_values(self):
        """All element types should have correct string values."""
        assert ElementType.BUTTON.value == "BUTTON"
        assert ElementType.LINK.value == "LINK"
        assert ElementType.INPUT.value == "INPUT"
        assert ElementType.SELECT.value == "SELECT"
        assert ElementType.CHECKBOX.value == "CHECKBOX"

    def test_annotation_mode_values(self):
        """Annotation modes should have correct values."""
        assert AnnotationMode.FULL.value == "FULL"
        assert AnnotationMode.NONE.value == "NONE"
        assert AnnotationMode.BOUNDING_BOX.value == "BOUNDING_BOX"


# ─────────────────────────────────────────────
# Screenshot Capture Tests
# ─────────────────────────────────────────────

class TestScreenshotCapture:
    """Tests for the ScreenshotManager."""

    def test_capture_viewport_returns_capture(self, mock_browser, vision_config):
        """Viewport capture should return a ScreenshotCapture."""
        manager = ScreenshotManager(mock_browser, vision_config)
        capture = manager.capture_viewport()
        
        assert isinstance(capture, ScreenshotCapture)
        assert capture.page_url == "https://example.com"
        assert capture.page_title == "Example Page"
        assert capture.is_full_page is False

    def test_capture_full_page(self, mock_browser, vision_config):
        """Full-page capture should set is_full_page flag."""
        manager = ScreenshotManager(mock_browser, vision_config)
        capture = manager.capture_full_page()
        assert capture.is_full_page is True

    def test_capture_with_browser_failure(self, mock_browser, vision_config):
        """Capture should handle browser failures gracefully."""
        mock_browser.capture_screenshot.return_value = MagicMock(success=False, data=None)
        manager = ScreenshotManager(mock_browser, vision_config)
        capture = manager.capture_viewport()
        assert isinstance(capture, ScreenshotCapture)
        # Should still get metadata even if screenshot fails
        assert capture.page_url == "https://example.com"


# ─────────────────────────────────────────────
# DOM Annotator Tests
# ─────────────────────────────────────────────

class TestDOMAnnotator:
    """Tests for the DOMAnnotator."""

    def test_extract_elements_parses_json(self, mock_browser, vision_config):
        """Element extraction should parse JavaScript JSON response."""
        mock_elements = [
            {
                "tag": "button",
                "type": "BUTTON",
                "bbox": {"x": 100, "y": 200, "width": 80, "height": 30},
                "label": "Click Me",
                "selector": "button.primary",
                "is_visible": True,
                "is_enabled": True,
                "attributes": {"id": "btn1"},
            },
            {
                "tag": "a",
                "type": "LINK",
                "bbox": {"x": 50, "y": 300, "width": 120, "height": 20},
                "label": "Learn More",
                "selector": "a.learn",
                "is_visible": True,
                "is_enabled": True,
                "attributes": {"href": "/learn"},
            },
        ]
        mock_browser.execute_javascript.return_value = MagicMock(
            success=True, data=json.dumps(mock_elements)
        )

        annotator = DOMAnnotator(mock_browser, vision_config)
        elements = annotator.extract_elements()
        
        assert len(elements) == 2
        assert elements[0].element_type == ElementType.BUTTON
        assert elements[0].label == "Click Me"
        assert elements[1].element_type == ElementType.LINK

    def test_extract_elements_sorted_by_position(self, mock_browser, vision_config):
        """Extracted elements should be sorted top-to-bottom."""
        mock_elements = [
            {"tag": "a", "type": "LINK", "bbox": {"x": 0, "y": 500, "width": 100, "height": 20},
             "label": "Bottom", "selector": "a.b", "is_visible": True, "is_enabled": True, "attributes": {}},
            {"tag": "button", "type": "BUTTON", "bbox": {"x": 0, "y": 100, "width": 100, "height": 20},
             "label": "Top", "selector": "button.t", "is_visible": True, "is_enabled": True, "attributes": {}},
        ]
        mock_browser.execute_javascript.return_value = MagicMock(
            success=True, data=json.dumps(mock_elements)
        )

        annotator = DOMAnnotator(mock_browser, vision_config)
        elements = annotator.extract_elements()
        
        assert elements[0].label == "Top"
        assert elements[1].label == "Bottom"

    def test_extract_elements_handles_empty_response(self, mock_browser, vision_config):
        """Should handle empty JavaScript response gracefully."""
        mock_browser.execute_javascript.return_value = MagicMock(success=True, data="[]")
        annotator = DOMAnnotator(mock_browser, vision_config)
        elements = annotator.extract_elements()
        assert elements == []

    def test_extract_elements_handles_failure(self, mock_browser, vision_config):
        """Should handle JavaScript execution failure gracefully."""
        mock_browser.execute_javascript.return_value = MagicMock(success=False, data=None)
        annotator = DOMAnnotator(mock_browser, vision_config)
        elements = annotator.extract_elements()
        assert elements == []

    def test_annotate_screenshot_no_op_for_none_mode(self, mock_browser):
        """Annotation should be skipped when mode is NONE."""
        config = VisionConfig(annotation_mode=AnnotationMode.NONE)
        annotator = DOMAnnotator(mock_browser, config)
        
        original = ScreenshotCapture(image_bytes=b"test")
        result = annotator.annotate_screenshot(original, [])
        assert result is original  # Same object, no annotation

    def test_annotate_screenshot_empty_image(self, mock_browser, vision_config):
        """Annotation should handle empty image bytes gracefully."""
        annotator = DOMAnnotator(mock_browser, vision_config)
        capture = ScreenshotCapture(image_bytes=b"")
        result = annotator.annotate_screenshot(capture, [VisualElement()])
        assert result is capture  # Returns original when no image data

    def test_max_elements_limit(self, mock_browser):
        """Should respect max_elements_to_annotate limit."""
        config = VisionConfig(max_elements_to_annotate=2)
        mock_elements = [
            {"tag": "button", "type": "BUTTON", "bbox": {"x": 0, "y": i * 10, "width": 50, "height": 10},
             "label": f"btn{i}", "selector": f"button.b{i}", "is_visible": True, "is_enabled": True, "attributes": {}}
            for i in range(10)
        ]
        mock_browser.execute_javascript.return_value = MagicMock(
            success=True, data=json.dumps(mock_elements)
        )
        
        annotator = DOMAnnotator(mock_browser, config)
        elements = annotator.extract_elements()
        assert len(elements) == 2


# ─────────────────────────────────────────────
# Visual Differ Tests
# ─────────────────────────────────────────────

class TestVisualDiffer:
    """Tests for the VisualDiffer."""

    def _make_solid_image(self, color, width=100, height=100):
        """Helper to create a solid color PNG image."""
        try:
            from PIL import Image
            img = Image.new("RGB", (width, height), color)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        except ImportError:
            pytest.skip("Pillow required for visual differ tests")

    def test_identical_images_no_change(self):
        """Identical images should show 0% change."""
        config = VisionConfig(save_captures_to_disk=False, diff_threshold=1.0)
        differ = VisualDiffer(config)
        
        img_data = self._make_solid_image((255, 0, 0))
        before = ScreenshotCapture(image_bytes=img_data)
        after = ScreenshotCapture(image_bytes=img_data)
        
        result = differ.compare(before, after, "test_action")
        assert result.change_detected is False
        assert result.change_percentage == 0.0

    def test_completely_different_images(self):
        """Completely different images should show high change percentage."""
        config = VisionConfig(save_captures_to_disk=False, diff_threshold=1.0)
        differ = VisualDiffer(config)
        
        before_data = self._make_solid_image((255, 0, 0))   # Red
        after_data = self._make_solid_image((0, 0, 255))     # Blue
        
        before = ScreenshotCapture(image_bytes=before_data)
        after = ScreenshotCapture(image_bytes=after_data)
        
        result = differ.compare(before, after, "navigation")
        assert result.change_detected is True
        assert result.change_percentage > 90.0

    def test_partial_change(self):
        """Partially different images should show proportional change."""
        try:
            from PIL import Image
        except ImportError:
            pytest.skip("Pillow required")
        
        config = VisionConfig(save_captures_to_disk=False, diff_threshold=1.0)
        differ = VisualDiffer(config)
        
        # Create before image (all white)
        before_img = Image.new("RGB", (100, 100), (255, 255, 255))
        buf = io.BytesIO()
        before_img.save(buf, format="PNG")
        before_data = buf.getvalue()
        
        # Create after image (half white, half black)
        after_img = Image.new("RGB", (100, 100), (255, 255, 255))
        for x in range(50):
            for y in range(100):
                after_img.putpixel((x, y), (0, 0, 0))
        buf = io.BytesIO()
        after_img.save(buf, format="PNG")
        after_data = buf.getvalue()
        
        before = ScreenshotCapture(image_bytes=before_data)
        after = ScreenshotCapture(image_bytes=after_data)
        
        result = differ.compare(before, after, "click")
        assert result.change_detected is True
        # Approximately 50% changed
        assert 40.0 < result.change_percentage < 60.0

    def test_empty_image_bytes(self):
        """Should handle missing image data gracefully."""
        config = VisionConfig(save_captures_to_disk=False)
        differ = VisualDiffer(config)
        
        before = ScreenshotCapture(image_bytes=b"")
        after = ScreenshotCapture(image_bytes=b"")
        
        result = differ.compare(before, after, "test")
        assert result.change_detected is False
        assert "Cannot compare" in result.change_description

    def test_different_sized_images(self):
        """Should handle images of different dimensions."""
        config = VisionConfig(save_captures_to_disk=False, diff_threshold=1.0)
        differ = VisualDiffer(config)
        
        before_data = self._make_solid_image((255, 0, 0), width=100, height=100)
        after_data = self._make_solid_image((0, 255, 0), width=200, height=150)
        
        before = ScreenshotCapture(image_bytes=before_data)
        after = ScreenshotCapture(image_bytes=after_data)
        
        result = differ.compare(before, after, "resize")
        # Should still complete without error
        assert isinstance(result, VisualVerification)

    def test_change_description_categories(self):
        """Change descriptions should vary by change magnitude."""
        config = VisionConfig(save_captures_to_disk=False)
        differ = VisualDiffer(config)
        
        before = ScreenshotCapture(page_url="https://a.com")
        after = ScreenshotCapture(page_url="https://b.com")
        
        # Test various change levels
        desc_0 = differ._describe_change(0.05, before, after)
        assert "No significant" in desc_0
        
        desc_5 = differ._describe_change(5.0, before, after)
        assert "Moderate" in desc_5
        
        desc_60 = differ._describe_change(60.0, before, after)
        assert "Major" in desc_60
        assert "Navigation" in desc_60  # URLs differ


# ─────────────────────────────────────────────
# Vision Pipeline Tests
# ─────────────────────────────────────────────

class TestVisionPipeline:
    """Tests for the VisionPipeline orchestrator."""

    def test_capture_and_annotate(self, mock_browser, vision_config):
        """capture_and_annotate should return a capture and elements."""
        mock_browser.execute_javascript.return_value = MagicMock(success=True, data="[]")
        
        pipeline = VisionPipeline(mock_browser, vision_config)
        capture, elements = pipeline.capture_and_annotate()
        
        assert isinstance(capture, ScreenshotCapture)
        assert isinstance(elements, list)

    def test_capture_raw(self, mock_browser, vision_config):
        """capture_raw should return unannotated screenshot."""
        pipeline = VisionPipeline(mock_browser, vision_config)
        capture = pipeline.capture_raw()
        assert isinstance(capture, ScreenshotCapture)

    def test_detect_elements(self, mock_browser, vision_config):
        """detect_elements should return element list."""
        mock_browser.execute_javascript.return_value = MagicMock(success=True, data="[]")
        pipeline = VisionPipeline(mock_browser, vision_config)
        elements = pipeline.detect_elements()
        assert isinstance(elements, list)

    def test_get_visual_state_summary(self, mock_browser, vision_config):
        """get_visual_state_summary should return structured summary."""
        mock_browser.execute_javascript.return_value = MagicMock(success=True, data="[]")
        pipeline = VisionPipeline(mock_browser, vision_config)
        summary = pipeline.get_visual_state_summary()
        
        assert "page_url" in summary
        assert "total_interactive_elements" in summary
        assert "element_type_counts" in summary

    def test_verify_action(self, mock_browser, vision_config):
        """verify_action should compare before/after captures."""
        pipeline = VisionPipeline(mock_browser, vision_config)
        
        before = ScreenshotCapture(image_bytes=b"")
        after = ScreenshotCapture(image_bytes=b"")
        
        result = pipeline.verify_action("click", before, after)
        assert isinstance(result, VisualVerification)

    def test_capture_before_action(self, mock_browser, vision_config):
        """capture_before_action should store reference capture."""
        pipeline = VisionPipeline(mock_browser, vision_config)
        capture = pipeline.capture_before_action()
        assert isinstance(capture, ScreenshotCapture)
        assert pipeline._last_capture is capture

    def test_get_element_at_position(self, mock_browser, vision_config):
        """get_element_at_position should find the smallest matching element."""
        pipeline = VisionPipeline(mock_browser, vision_config)
        
        elements = [
            VisualElement(
                element_type=ElementType.BUTTON,
                bbox=BoundingBox(x=0, y=0, width=200, height=100),
                label="Big button",
            ),
            VisualElement(
                element_type=ElementType.LINK,
                bbox=BoundingBox(x=50, y=30, width=40, height=20),
                label="Small link",
            ),
        ]
        
        result = pipeline.get_element_at_position(60, 40, elements)
        assert result is not None
        assert result.label == "Small link"  # Smallest matching element

    def test_get_element_at_position_no_match(self, mock_browser, vision_config):
        """get_element_at_position should return None for unmatched position."""
        pipeline = VisionPipeline(mock_browser, vision_config)
        elements = [
            VisualElement(bbox=BoundingBox(x=100, y=100, width=50, height=50)),
        ]
        result = pipeline.get_element_at_position(0, 0, elements)
        assert result is None
