"""Data models for the Vision Intelligence Platform."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from core.utils.id_generator import generate_id
from core.utils.time_utils import utc_isoformat


class VisionAnalysisType(str, Enum):
    """Types of visual analysis performed by the Vision Platform."""
    GENERAL_IMAGE = "general_image"
    OCR_TEXT = "ocr_text"
    SCREENSHOT_UI = "screenshot_ui"
    DOCUMENT_LAYOUT = "document_layout"
    CHART_GRAPH = "chart_graph"
    TABLE_RECOGNITION = "table_recognition"
    DIAGRAM_INTERPRETATION = "diagram_interpretation"


@dataclass
class BoundingBox:
    """Bounding box coordinates (normalized 0.0 to 1.0 or pixel integer)."""
    x_min: float = 0.0
    y_min: float = 0.0
    x_max: float = 1.0
    y_max: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x_min": self.x_min,
            "y_min": self.y_min,
            "x_max": self.x_max,
            "y_max": self.y_max,
        }


@dataclass
class OCRTextRegion:
    """Extracted text block region with confidence."""
    text: str = ""
    confidence: float = 0.90
    bounding_box: BoundingBox = field(default_factory=BoundingBox)
    line_number: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bounding_box": self.bounding_box.to_dict(),
            "line_number": self.line_number,
        }


@dataclass
class DetectedRegion:
    """Generic detected visual region or UI element."""
    region_id: str = field(default_factory=lambda: generate_id("reg_"))
    label: str = ""
    category: str = "text"  # 'text', 'button', 'input', 'header', 'image', 'table', 'chart'
    confidence: float = 0.85
    bounding_box: BoundingBox = field(default_factory=BoundingBox)
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "region_id": self.region_id,
            "label": self.label,
            "category": self.category,
            "confidence": self.confidence,
            "bounding_box": self.bounding_box.to_dict(),
            "attributes": self.attributes,
        }


@dataclass
class VisualTable:
    """Structured table extracted from visual data."""
    table_id: str = field(default_factory=lambda: generate_id("vtbl_"))
    caption: Optional[str] = None
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    confidence: float = 0.88
    bounding_box: Optional[BoundingBox] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_id": self.table_id,
            "caption": self.caption,
            "headers": self.headers,
            "rows": self.rows,
            "confidence": self.confidence,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
        }


@dataclass
class VisualChart:
    """Structured chart/graph data extracted from visual image."""
    chart_id: str = field(default_factory=lambda: generate_id("vch_"))
    chart_type: str = "bar"  # 'bar', 'line', 'pie', 'scatter'
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    series_data: Dict[str, List[float]] = field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "chart_type": self.chart_type,
            "title": self.title,
            "x_label": self.x_label,
            "y_label": self.y_label,
            "series_data": self.series_data,
            "summary": self.summary,
        }


@dataclass
class DiagramNode:
    """Node in an interpreted flowchart or diagram."""
    node_id: str = field(default_factory=lambda: generate_id("dnode_"))
    label: str = ""
    node_type: str = "process"  # 'start', 'process', 'decision', 'end', 'entity'
    bounding_box: Optional[BoundingBox] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "node_type": self.node_type,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
        }


@dataclass
class DiagramEdge:
    """Directed connection between diagram nodes."""
    edge_id: str = field(default_factory=lambda: generate_id("dedge_"))
    source_node_id: str = ""
    target_node_id: str = ""
    label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "label": self.label,
        }


@dataclass
class VisionMetrics:
    """Telemetry metrics for vision analysis."""
    processing_time_ms: float = 0.0
    image_width: int = 0
    image_height: int = 0
    regions_detected_count: int = 0
    ocr_word_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "processing_time_ms": self.processing_time_ms,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "regions_detected_count": self.regions_detected_count,
            "ocr_word_count": self.ocr_word_count,
        }


@dataclass
class NormalizedVisionResult:
    """Unified container model produced by all visual analysis components."""
    analysis_id: str = field(default_factory=lambda: generate_id("vis_"))
    source_path_or_url: str = ""
    analysis_type: VisionAnalysisType = VisionAnalysisType.GENERAL_IMAGE
    caption: str = ""
    extracted_text: str = ""
    ocr_regions: List[OCRTextRegion] = field(default_factory=list)
    detected_regions: List[DetectedRegion] = field(default_factory=list)
    tables: List[VisualTable] = field(default_factory=list)
    charts: List[VisualChart] = field(default_factory=list)
    diagram_nodes: List[DiagramNode] = field(default_factory=list)
    diagram_edges: List[DiagramEdge] = field(default_factory=list)
    overall_confidence: float = 0.90
    metrics: VisionMetrics = field(default_factory=VisionMetrics)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_isoformat)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "source_path_or_url": self.source_path_or_url,
            "analysis_type": self.analysis_type.value,
            "caption": self.caption,
            "extracted_text": self.extracted_text,
            "ocr_regions": [r.to_dict() for r in self.ocr_regions],
            "detected_regions": [dr.to_dict() for dr in self.detected_regions],
            "tables": [t.to_dict() for t in self.tables],
            "charts": [c.to_dict() for c in self.charts],
            "diagram_nodes": [dn.to_dict() for dn in self.diagram_nodes],
            "diagram_edges": [de.to_dict() for de in self.diagram_edges],
            "overall_confidence": self.overall_confidence,
            "metrics": self.metrics.to_dict(),
            "metadata": self.metadata,
            "created_at": self.created_at,
        }
