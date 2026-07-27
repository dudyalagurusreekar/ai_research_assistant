"""Default Vision Provider strategy implementation using Pillow."""

import os
import time
import asyncio
from typing import Any
from tools.vision.interfaces.vision_interfaces import IVisionProvider
from tools.vision.models.vision_models import (
    NormalizedVisionResult,
    VisionAnalysisType,
    VisionMetrics,
    DetectedRegion,
    BoundingBox,
)
from infrastructure.logging.logger import StructuredLogger

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class DefaultVisionProvider(IVisionProvider):
    """Default fallback vision engine provider handling PIL images and file paths."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("DefaultVisionProvider")

    @property
    def provider_name(self) -> str:
        return "default_vision"

    async def analyze(self, image_input: Any, analysis_type: VisionAnalysisType) -> NormalizedVisionResult:
        """Analyze image input and produce NormalizedVisionResult."""
        start_time = time.time()
        self._logger.info(f"Analyzing image input (type={analysis_type.value})")

        img_width = 800
        img_height = 600
        src_path = str(image_input) if isinstance(image_input, str) else "in_memory_image"

        if HAS_PIL and isinstance(image_input, str) and os.path.exists(image_input):
            try:
                with Image.open(image_input) as img:
                    img_width, img_height = img.size
            except Exception:
                pass

        proc_time_ms = (time.time() - start_time) * 1000
        metrics = VisionMetrics(
            processing_time_ms=round(proc_time_ms, 2),
            image_width=img_width,
            image_height=img_height,
            regions_detected_count=1,
        )

        result = NormalizedVisionResult(
            source_path_or_url=src_path,
            analysis_type=analysis_type,
            caption=f"Visual image ({analysis_type.value}): {img_width}x{img_height}",
            detected_regions=[
                DetectedRegion(
                    label="Main Content Area",
                    category="general",
                    bounding_box=BoundingBox(x_min=0.0, y_min=0.0, x_max=1.0, y_max=1.0),
                )
            ],
            metrics=metrics,
        )
        return result
