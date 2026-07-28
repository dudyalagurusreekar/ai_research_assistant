"""Unified VisionToolFacade for the Vision Intelligence Platform."""

import json
from typing import Dict, List, Any, Optional

from core.interfaces.tool import ITool
from core.models.metadata import ToolMetadata
from core.models.tool_result import ToolResult
from core.models.event import Event
from core.events import AsyncEventBus
from tools.vision.models.vision_models import (
    NormalizedVisionResult,
    VisionAnalysisType,
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
from infrastructure.logging.logger import StructuredLogger


class VisionToolFacade(ITool):
    """Public unified API facade for the Vision Intelligence Platform."""

    name = "vision_tool"
    description = "Unified visual understanding tool for image analysis, OCR, screenshots, layout, charts, tables, and diagrams."

    def __init__(
        self,
        registry: Optional[VisionProviderRegistry] = None,
        processor: Optional[ImageProcessor] = None,
        layout_analyzer: Optional[LayoutAnalyzer] = None,
        chart_analyzer: Optional[ChartAnalyzer] = None,
        table_recognizer: Optional[TableRecognizer] = None,
        diagram_interpreter: Optional[DiagramInterpreter] = None,
        screenshot_analyzer: Optional[ScreenshotAnalyzer] = None,
        event_bus: Optional[AsyncEventBus] = None,
        document_facade: Optional[Any] = None,
        memory_facade: Optional[Any] = None,
    ) -> None:
        self.name = "vision_tool"
        self._logger = StructuredLogger("VisionToolFacade")
        self._event_bus = event_bus or AsyncEventBus()
        self._document_facade = document_facade
        self._memory_facade = memory_facade

        self._registry = registry or VisionProviderRegistry()
        if not self._registry.list_providers():
            self._registry.register(DefaultVisionProvider())
            self._registry.register(TesseractOCRProvider())

        self._processor = processor or ImageProcessor()
        self._layout_analyzer = layout_analyzer or LayoutAnalyzer()
        self._chart_analyzer = chart_analyzer or ChartAnalyzer()
        self._table_recognizer = table_recognizer or TableRecognizer()
        self._diagram_interpreter = diagram_interpreter or DiagramInterpreter()
        self._screenshot_analyzer = screenshot_analyzer or ScreenshotAnalyzer()

        self._metadata = ToolMetadata(
            name="vision_tool",
            version="1.0.0",
            description="Unified visual understanding tool for image analysis, OCR, screenshots, layout, charts, tables, and diagrams.",
            capabilities=["vision", "ocr", "screenshot_ui", "chart_analysis", "table_recognition", "diagram_interpretation"],
            parameters_schema={
                "action": "Action to perform ('analyze', 'ocr', 'screenshot', 'chart', 'table', 'diagram')",
                "image": "Image file path or URL string",
                "analysis_type": "Vision analysis type",
            },
            tags=["vision", "ocr", "screenshot", "layout"],
            is_async=True,
            enabled=True,
        )

    @property
    def metadata(self) -> ToolMetadata:
        """Return tool metadata descriptor."""
        return self._metadata

    async def forward(self, action: str = "analyze", **kwargs) -> str:
        """Standard tool execution wrapper returning JSON string."""
        try:
            img_input = kwargs.get("image", kwargs.get("path", kwargs.get("url", "")))
            if action in ["analyze", "image"]:
                a_type = kwargs.get("analysis_type", VisionAnalysisType.GENERAL_IMAGE)
                if isinstance(a_type, str):
                    a_type = VisionAnalysisType(a_type)
                res = await self.analyze_image(img_input, analysis_type=a_type)
                return json.dumps(res.to_dict(), indent=2)
            elif action in ["ocr", "text"]:
                res_ocr = await self.extract_ocr(img_input)
                return json.dumps(res_ocr.to_dict(), indent=2)
            elif action in ["screenshot", "ui"]:
                res_ss = await self.analyze_screenshot(img_input)
                return json.dumps(res_ss.to_dict(), indent=2)
            elif action in ["chart", "graph"]:
                charts = await self.analyze_chart(img_input)
                return json.dumps([c.to_dict() for c in charts], indent=2)
            elif action in ["table", "grid"]:
                tables = await self.recognize_table(img_input)
                return json.dumps([t.to_dict() for t in tables], indent=2)
            elif action in ["diagram", "flowchart"]:
                nodes, edges = await self.interpret_diagram(img_input)
                return json.dumps({
                    "nodes": [n.to_dict() for n in nodes],
                    "edges": [e.to_dict() for e in edges],
                }, indent=2)
            else:
                return json.dumps({"error": f"Unknown vision action '{action}'"}, indent=2)
        except Exception as e:
            self._logger.error(f"Error in VisionToolFacade.forward action '{action}': {e}")
            return json.dumps({"error": str(e)}, indent=2)

    async def execute(self, parameters: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        """Execute method returning ToolResult object conforming to ITool interface."""
        params = dict(parameters or {})
        params.update(kwargs)
        action = params.get("action", "analyze")
        try:
            output_json = await self.forward(action=action, **params)
            data = json.loads(output_json)
            if isinstance(data, dict) and "error" in data:
                return ToolResult.error(error_message=data["error"])
            return ToolResult.success(data=data)
        except Exception as e:
            return ToolResult.error(error_message=str(e))

    async def analyze_image(self, image_input: Any, analysis_type: VisionAnalysisType = VisionAnalysisType.GENERAL_IMAGE) -> NormalizedVisionResult:
        """Analyze generic image using provider strategies."""
        try:
            await self._publish_event("vision.started", {"image": str(image_input), "type": analysis_type.value})
            
            # Preprocess image
            proc_meta = await self._processor.preprocess(image_input)
            await self._publish_event("image.processed", proc_meta)

            provider = self._registry.get_provider("default_vision") or self._registry.list_providers()[0]
            result = await provider.analyze(image_input, analysis_type)

            # Detect page layout if document image
            if analysis_type in [VisionAnalysisType.DOCUMENT_LAYOUT, VisionAnalysisType.GENERAL_IMAGE]:
                layout_regions = await self._layout_analyzer.analyze_layout(image_input)
                result.detected_regions.extend(layout_regions)
                await self._publish_event("layout.detected", {"regions_count": len(layout_regions)})

            # Ingest into memory if available
            await self._auto_ingest_memory(result)

            await self._publish_event("vision.completed", {"analysis_id": result.analysis_id})
            return result
        except Exception as e:
            await self._publish_event("vision.failed", {"action": "analyze", "error": str(e)})
            raise

    async def extract_ocr(self, image_input: Any) -> NormalizedVisionResult:
        """Extract text using OCR engine."""
        try:
            await self._publish_event("vision.started", {"image": str(image_input), "type": "ocr_text"})
            provider = self._registry.get_provider("tesseract_ocr") or self._registry.list_providers()[0]
            result = await provider.analyze(image_input, VisionAnalysisType.OCR_TEXT)
            await self._publish_event("ocr.completed", {"words_count": result.metrics.ocr_word_count})

            await self._auto_ingest_memory(result)
            await self._publish_event("vision.completed", {"analysis_id": result.analysis_id})
            return result
        except Exception as e:
            await self._publish_event("vision.failed", {"action": "ocr", "error": str(e)})
            raise

    async def analyze_screenshot(self, image_input: Any) -> NormalizedVisionResult:
        """Analyze browser screenshot for UI elements."""
        try:
            await self._publish_event("vision.started", {"image": str(image_input), "type": "screenshot_ui"})
            result = await self._screenshot_analyzer.analyze_screenshot(image_input)
            await self._publish_event("screenshot.analyzed", {"regions_count": len(result.detected_regions)})

            await self._auto_ingest_memory(result)
            await self._publish_event("vision.completed", {"analysis_id": result.analysis_id})
            return result
        except Exception as e:
            await self._publish_event("vision.failed", {"action": "screenshot", "error": str(e)})
            raise

    async def analyze_chart(self, image_input: Any) -> List[VisualChart]:
        """Extract chart and graph data."""
        try:
            charts = await self._chart_analyzer.analyze_chart(image_input)
            await self._publish_event("chart.analyzed", {"charts_count": len(charts)})
            return charts
        except Exception as e:
            await self._publish_event("vision.failed", {"action": "chart", "error": str(e)})
            raise

    async def recognize_table(self, image_input: Any) -> List[VisualTable]:
        """Recognize visual table grid structure."""
        try:
            tables = await self._table_recognizer.recognize_tables(image_input)
            await self._publish_event("table.recognized", {"tables_count": len(tables)})
            return tables
        except Exception as e:
            await self._publish_event("vision.failed", {"action": "table", "error": str(e)})
            raise

    async def interpret_diagram(self, image_input: Any) -> tuple[List[DiagramNode], List[DiagramEdge]]:
        """Interpret flowchart nodes and edges."""
        try:
            nodes, edges = await self._diagram_interpreter.interpret_diagram(image_input)
            await self._publish_event("diagram.interpreted", {"nodes_count": len(nodes), "edges_count": len(edges)})
            return nodes, edges
        except Exception as e:
            await self._publish_event("vision.failed", {"action": "diagram", "error": str(e)})
            raise

    async def _auto_ingest_memory(self, result: NormalizedVisionResult) -> None:
        """Publish vision result into Memory Platform if memory_facade is attached."""
        if self._memory_facade:
            try:
                content_desc = result.caption or result.extracted_text or f"Vision analysis of {result.source_path_or_url}"
                await self._memory_facade.remember(
                    content=f"Visual Analysis ({result.analysis_type.value}): {content_desc[:400]}",
                    memory_type="knowledge",
                    tags=["vision", result.analysis_type.value],
                    metadata={"analysis_id": result.analysis_id, "source": result.source_path_or_url},
                )
            except Exception as me:
                self._logger.warning(f"Error persisting vision memory: {me}")

    async def _publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish domain event over AsyncEventBus."""
        if self._event_bus:
            try:
                event_obj = Event(
                    event_type=event_type,
                    source="VisionToolFacade",
                    payload=payload,
                )
                await self._event_bus.publish(event_obj)
            except Exception as e:
                self._logger.warning(f"Error publishing vision event '{event_type}': {e}")
