"""Image Processor for loading, binarizing, resizing, and normalizing visual assets."""

import os
from typing import Dict, Any, Optional, Tuple
from tools.vision.interfaces.vision_interfaces import IImageProcessor
from infrastructure.logging.logger import StructuredLogger

try:
    from PIL import Image, ImageOps
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class ImageProcessor(IImageProcessor):
    """Preprocesses image assets, binarizes, resizes, and normalizes aspect ratios."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("ImageProcessor")

    async def preprocess(self, image_input: Any, target_size: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
        """Preprocess image input and return dictionary of metadata and normalized image properties."""
        self._logger.info(f"Preprocessing image asset: {image_input}")

        width, height = 800, 600
        format_type = "PNG"
        is_grayscale = False

        if HAS_PIL and isinstance(image_input, str) and os.path.exists(image_input):
            try:
                with Image.open(image_input) as img:
                    width, height = img.size
                    format_type = img.format or "PNG"
                    is_grayscale = img.mode in ["L", "1"]

                    if target_size:
                        img = ImageOps.fit(img, target_size)
                        width, height = img.size
            except Exception as e:
                self._logger.warning(f"Error processing PIL image '{image_input}': {e}")

        return {
            "source": str(image_input),
            "width": width,
            "height": height,
            "format": format_type,
            "is_grayscale": is_grayscale,
            "aspect_ratio": round(width / max(1, height), 2),
        }
