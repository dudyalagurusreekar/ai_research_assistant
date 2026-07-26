"""Vision Pipeline Package.

Provides screenshot-based visual perception capabilities for the autonomous
browser agent, including element detection, annotation, and action verification.
"""

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

__all__ = [
    # Models
    "AnnotationMode",
    "BoundingBox",
    "ElementType",
    "ScreenshotCapture",
    "VisualElement",
    "VisualVerification",
    "VisionConfig",
    # Components
    "ScreenshotManager",
    "DOMAnnotator",
    "VisualDiffer",
    # Pipeline
    "VisionPipeline",
]
