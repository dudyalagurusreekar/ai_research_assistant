"""Comprehensive Unit, Integration, Concurrency, and End-to-End Tests for Phase 8 Vision Intelligence Platform."""

import asyncio
import os
import tempfile
import pytest

from tools.vision.facade.facade import VisionToolFacade
from tools.vision.models.vision_models import (
    NormalizedVisionResult,
    VisionAnalysisType,
    DetectedRegion,
    BoundingBox,
    OCRTextRegion,
    VisualTable,
    VisualChart,
    DiagramNode,
    DiagramEdge,
)
from tools.vision.registry.vision_registry import VisionProviderRegistry
from tools.vision.providers.default_vision_provider import DefaultVisionProvider
from tools.vision.providers.ocr_provider import TesseractOCRProvider
from tools.vision.processor.image_processor import ImageProcessor
from tools.vision.analyzer.layout_analyzer import LayoutAnalyzer
from tools.vision.charts.chart_analyzer import ChartAnalyzer
from tools.vision.tables.table_recognizer import TableRecognizer
from tools.vision.diagrams.diagram_interpreter import DiagramInterpreter
from tools.vision.screenshots.screenshot_analyzer import ScreenshotAnalyzer
from tools.vision.tool import VisionTool
from core.events import AsyncEventBus


def test_vision_provider_registry():
    """Verify vision provider strategy registration and lookup."""
    registry = VisionProviderRegistry()
    default_p = DefaultVisionProvider()
    ocr_p = TesseractOCRProvider()

    registry.register(default_p)
    registry.register(ocr_p)

    assert registry.get_provider("default_vision") is not None
    assert registry.get_provider("tesseract_ocr") is not None
    assert len(registry.list_providers()) == 2


def test_image_processor():
    """Verify image preprocessing, resizing, and aspect ratio calculation."""
    async def _test():
        processor = ImageProcessor()
        res = await processor.preprocess("dummy_image.png", target_size=(400, 300))

        assert res["width"] > 0
        assert res["height"] > 0
        assert "aspect_ratio" in res

    asyncio.run(_test())


def test_layout_analyzer():
    """Verify page layout region segmentation."""
    async def _test():
        analyzer = LayoutAnalyzer()
        regions = await analyzer.analyze_layout("sample_page.png")

        assert len(regions) >= 4
        categories = [r.category for r in regions]
        assert "header" in categories
        assert "footer" in categories

    asyncio.run(_test())


def test_ocr_provider():
    """Verify OCR text region extraction."""
    async def _test():
        ocr = TesseractOCRProvider()
        res = await ocr.analyze("document.png", VisionAnalysisType.OCR_TEXT)

        assert res.analysis_type == VisionAnalysisType.OCR_TEXT
        assert len(res.extracted_text) > 0
        assert res.metrics.ocr_word_count > 0

    asyncio.run(_test())


def test_chart_analyzer():
    """Verify chart type and data series extraction."""
    async def _test():
        analyzer = ChartAnalyzer()
        charts = await analyzer.analyze_chart("chart.png")

        assert len(charts) == 1
        chart = charts[0]
        assert chart.chart_type == "bar"
        assert len(chart.series_data) >= 2

    asyncio.run(_test())


def test_table_recognizer():
    """Verify visual table grid parsing."""
    async def _test():
        recognizer = TableRecognizer()
        tables = await recognizer.recognize_tables("table_screenshot.png")

        assert len(tables) == 1
        table = tables[0]
        assert len(table.headers) == 3
        assert len(table.rows) >= 5

    asyncio.run(_test())


def test_diagram_interpreter():
    """Verify flowchart nodes and directed edges resolution."""
    async def _test():
        interpreter = DiagramInterpreter()
        nodes, edges = await interpreter.interpret_diagram("flowchart.png")

        assert len(nodes) == 3
        assert len(edges) == 2
        assert edges[0].source_node_id == nodes[0].node_id

    asyncio.run(_test())


def test_screenshot_analyzer():
    """Verify browser screenshot UI element detection."""
    async def _test():
        analyzer = ScreenshotAnalyzer()
        res = await analyzer.analyze_screenshot("viewport.png")

        assert res.analysis_type == VisionAnalysisType.SCREENSHOT_UI
        assert len(res.detected_regions) >= 3
        categories = [r.category for r in res.detected_regions]
        assert "input" in categories
        assert "button" in categories

    asyncio.run(_test())


def test_vision_facade_end_to_end_and_events():
    """Verify VisionToolFacade unified APIs, memory ingestion, and AsyncEventBus notifications."""
    async def _test():
        bus = AsyncEventBus()
        events_fired = []

        async def _on_event(evt):
            events_fired.append(evt.event_type)

        bus.subscribe("vision.started", _on_event)
        bus.subscribe("image.processed", _on_event)
        bus.subscribe("layout.detected", _on_event)
        bus.subscribe("ocr.completed", _on_event)
        bus.subscribe("screenshot.analyzed", _on_event)
        bus.subscribe("vision.completed", _on_event)

        facade = VisionToolFacade(event_bus=bus)

        # 1. Analyze Image API
        img_res = await facade.analyze_image("test_image.png")
        assert img_res.analysis_id != ""

        # 2. Extract OCR API
        ocr_res = await facade.extract_ocr("doc_scan.png")
        assert ocr_res.extracted_text != ""

        # 3. Screenshot API
        ss_res = await facade.analyze_screenshot("browser_view.png")
        assert len(ss_res.detected_regions) > 0

        # Wait briefly for async events
        await asyncio.sleep(0.05)
        assert "vision.started" in events_fired
        assert "image.processed" in events_fired
        assert "layout.detected" in events_fired
        assert "ocr.completed" in events_fired
        assert "screenshot.analyzed" in events_fired
        assert "vision.completed" in events_fired

        # Test forward JSON method
        forward_json = await facade.forward(action="screenshot", image="viewport.png")
        assert "analysis_id" in forward_json

    asyncio.run(_test())


def test_smolagents_vision_tool_wrapper():
    """Verify smolagents VisionTool wrapper."""
    tool = VisionTool()
    res_str = tool.forward(action="screenshot", image="app_screenshot.png")
    assert "analysis_id" in res_str
