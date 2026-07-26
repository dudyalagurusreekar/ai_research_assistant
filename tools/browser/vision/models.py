"""Vision Pipeline Data Models.

Defines data structures for screenshot capture, visual element detection,
visual verification, and pipeline configuration.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class AnnotationMode(str, Enum):
    """How elements should be visually annotated on screenshots.

    Modes:
        BOUNDING_BOX: Draw rectangles around detected elements.
        LABEL_ONLY: Draw labels with element info without boxes.
        FULL: Draw both bounding boxes and labels.
        NONE: No annotations (raw screenshot).
    """

    BOUNDING_BOX = "BOUNDING_BOX"
    LABEL_ONLY = "LABEL_ONLY"
    FULL = "FULL"
    NONE = "NONE"


class ElementType(str, Enum):
    """Classification of detected visual elements.

    Types:
        BUTTON: Clickable button elements.
        LINK: Anchor/link elements.
        INPUT: Text input, textarea, and form fields.
        SELECT: Dropdown/select elements.
        CHECKBOX: Checkbox and radio inputs.
        IMAGE: Image elements.
        TEXT: Significant text blocks.
        INTERACTIVE: Other interactive elements.
        UNKNOWN: Unclassified elements.
    """

    BUTTON = "BUTTON"
    LINK = "LINK"
    INPUT = "INPUT"
    SELECT = "SELECT"
    CHECKBOX = "CHECKBOX"
    IMAGE = "IMAGE"
    TEXT = "TEXT"
    INTERACTIVE = "INTERACTIVE"
    UNKNOWN = "UNKNOWN"


@dataclass
class BoundingBox:
    """Rectangular region on a screenshot image.

    Coordinates use the CSS pixel coordinate system (origin at top-left).

    Attributes:
        x: Left edge X coordinate.
        y: Top edge Y coordinate.
        width: Width in pixels.
        height: Height in pixels.
    """

    x: float
    y: float
    width: float
    height: float

    @property
    def center(self) -> Tuple[float, float]:
        """Calculate the center point of this bounding box.

        Returns:
            Tuple of (center_x, center_y).
        """
        return (self.x + self.width / 2, self.y + self.height / 2)

    @property
    def area(self) -> float:
        """Calculate the area of this bounding box in square pixels.

        Returns:
            float: Area value.
        """
        return self.width * self.height

    def to_dict(self) -> Dict[str, float]:
        """Serialize bounding box to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "BoundingBox":
        """Reconstruct a BoundingBox from a dictionary.

        Args:
            data: Dictionary with x, y, width, height keys.

        Returns:
            BoundingBox instance.
        """
        return cls(
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 0),
            height=data.get("height", 0),
        )


@dataclass
class VisualElement:
    """A detected interactive or notable element on a page screenshot.

    Represents an element with its spatial position, classification,
    and metadata for visual grounding.

    Attributes:
        element_id: Unique identifier for this visual element.
        element_type: Classification of the element.
        bbox: Bounding box coordinates on the screenshot.
        label: Human-readable label or inner text.
        selector: CSS selector that targets this element.
        confidence: Detection confidence score (0.0 to 1.0).
        is_visible: Whether the element is visible in the viewport.
        is_enabled: Whether the element is interactable.
        attributes: Additional HTML attributes of interest.
    """

    element_id: str = field(default_factory=lambda: f"ve_{uuid.uuid4().hex[:6]}")
    element_type: ElementType = ElementType.UNKNOWN
    bbox: BoundingBox = field(default_factory=lambda: BoundingBox(0, 0, 0, 0))
    label: str = ""
    selector: str = ""
    confidence: float = 1.0
    is_visible: bool = True
    is_enabled: bool = True
    attributes: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize visual element to a JSON-compatible dictionary."""
        return {
            "element_id": self.element_id,
            "element_type": self.element_type.value,
            "bbox": self.bbox.to_dict(),
            "label": self.label,
            "selector": self.selector,
            "confidence": self.confidence,
            "is_visible": self.is_visible,
            "is_enabled": self.is_enabled,
            "attributes": self.attributes,
        }


@dataclass
class ScreenshotCapture:
    """A captured screenshot of a browser page.

    Stores the raw image data along with metadata about the capture context.

    Attributes:
        capture_id: Unique identifier for this capture.
        image_bytes: Raw PNG image data.
        width: Image width in pixels.
        height: Image height in pixels.
        page_url: URL of the page when captured.
        page_title: Title of the page when captured.
        timestamp: Unix timestamp of capture.
        is_full_page: Whether this is a full-page or viewport-only capture.
        file_path: Path where the screenshot was saved to disk (if saved).
    """

    capture_id: str = field(default_factory=lambda: f"cap_{uuid.uuid4().hex[:8]}")
    image_bytes: bytes = b""
    width: int = 0
    height: int = 0
    page_url: str = ""
    page_title: str = ""
    timestamp: float = field(default_factory=time.time)
    is_full_page: bool = False
    file_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize capture metadata (excludes image bytes for JSON safety)."""
        return {
            "capture_id": self.capture_id,
            "width": self.width,
            "height": self.height,
            "page_url": self.page_url,
            "page_title": self.page_title,
            "timestamp": self.timestamp,
            "is_full_page": self.is_full_page,
            "file_path": self.file_path,
            "size_bytes": len(self.image_bytes),
        }


@dataclass
class VisualVerification:
    """Result of visual verification comparing before/after screenshots.

    Used to verify whether a browser action had the expected visual effect.

    Attributes:
        action_name: The action that was executed between screenshots.
        before_capture: Screenshot taken before the action.
        after_capture: Screenshot taken after the action.
        change_detected: Whether significant visual change was detected.
        change_percentage: Percentage of pixels that changed (0.0 to 100.0).
        change_description: Human-readable description of what changed.
        diff_file_path: Path to the visual diff image (if generated).
    """

    action_name: str = ""
    before_capture: Optional[ScreenshotCapture] = None
    after_capture: Optional[ScreenshotCapture] = None
    change_detected: bool = False
    change_percentage: float = 0.0
    change_description: str = ""
    diff_file_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize verification result to dictionary."""
        return {
            "action_name": self.action_name,
            "before_capture": self.before_capture.to_dict() if self.before_capture else None,
            "after_capture": self.after_capture.to_dict() if self.after_capture else None,
            "change_detected": self.change_detected,
            "change_percentage": round(self.change_percentage, 2),
            "change_description": self.change_description,
            "diff_file_path": self.diff_file_path,
        }


@dataclass
class VisionConfig:
    """Configuration parameters for the Vision Pipeline.

    Attributes:
        capture_quality: JPEG quality for compressed captures (1-100).
        annotation_mode: How elements should be annotated on screenshots.
        diff_threshold: Minimum pixel change percentage to consider "changed" (0.0-100.0).
        max_elements_to_annotate: Maximum number of elements to annotate per screenshot.
        save_captures_to_disk: Whether to persist screenshots to the filesystem.
        capture_directory: Directory for saved screenshot files.
        box_color_rgb: RGB color tuple for annotation bounding boxes.
        label_font_size: Font size for annotation labels.
        enable_visual_verification: Whether to capture before/after for action verification.
    """

    capture_quality: int = 90
    annotation_mode: AnnotationMode = AnnotationMode.FULL
    diff_threshold: float = 1.0
    max_elements_to_annotate: int = 50
    save_captures_to_disk: bool = True
    capture_directory: str = ".browser_artifacts/screenshots"
    box_color_rgb: Tuple[int, int, int] = (255, 0, 0)
    label_font_size: int = 12
    enable_visual_verification: bool = False
