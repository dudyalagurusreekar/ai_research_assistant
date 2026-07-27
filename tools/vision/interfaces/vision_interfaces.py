"""Abstract interface contracts for the Vision Intelligence Platform."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from tools.vision.models.vision_models import (
    NormalizedVisionResult,
    VisionAnalysisType,
    DetectedRegion,
    VisualTable,
    VisualChart,
    DiagramNode,
    DiagramEdge,
)


class IVisionProvider(ABC):
    """Abstract strategy interface for pluggable vision and OCR engines."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier (e.g., 'default_vision', 'tesseract_ocr')."""
        pass

    @abstractmethod
    async def analyze(self, image_input: Any, analysis_type: VisionAnalysisType) -> NormalizedVisionResult:
        """Process image input and return NormalizedVisionResult."""
        pass


class IVisionProviderRegistry(ABC):
    """Abstract registry interface for vision providers."""

    @abstractmethod
    def register(self, provider: IVisionProvider) -> None:
        """Register a vision provider strategy."""
        pass

    @abstractmethod
    def get_provider(self, name: str) -> Optional[IVisionProvider]:
        """Get provider by name."""
        pass

    @abstractmethod
    def list_providers(self) -> List[IVisionProvider]:
        """List all registered providers."""
        pass


class IImageProcessor(ABC):
    """Abstract image preprocessing interface."""

    @abstractmethod
    async def preprocess(self, image_input: Any, target_size: Optional[tuple[int, int]] = None) -> Dict[str, Any]:
        """Preprocess image, extract dimensions, binarize, and normalize."""
        pass


class ILayoutAnalyzer(ABC):
    """Abstract document layout analysis interface."""

    @abstractmethod
    async def analyze_layout(self, image_input: Any) -> List[DetectedRegion]:
        """Segment page layout into structural regions."""
        pass


class IChartAnalyzer(ABC):
    """Abstract chart and graph interpretation interface."""

    @abstractmethod
    async def analyze_chart(self, image_input: Any) -> List[VisualChart]:
        """Extract chart type, titles, axis labels, and data series."""
        pass


class ITableRecognizer(ABC):
    """Abstract visual table recognition interface."""

    @abstractmethod
    async def recognize_tables(self, image_input: Any) -> List[VisualTable]:
        """Extract visual table grid and cells into structured tables."""
        pass


class IDiagramInterpreter(ABC):
    """Abstract flowchart and architecture diagram interpretation interface."""

    @abstractmethod
    async def interpret_diagram(self, image_input: Any) -> tuple[List[DiagramNode], List[DiagramEdge]]:
        """Identify flowchart nodes and directed edge relationships."""
        pass


class IScreenshotAnalyzer(ABC):
    """Abstract browser screenshot UI analysis interface."""

    @abstractmethod
    async def analyze_screenshot(self, image_input: Any) -> NormalizedVisionResult:
        """Analyze browser screenshot for UI elements and page layout."""
        pass
