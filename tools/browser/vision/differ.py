"""Visual Differ — Before/After Screenshot Comparison.

Compares two screenshots pixel-by-pixel to detect visual changes caused
by browser actions. Uses Pillow for image comparison without any
external computer vision dependencies.
"""

import io
import logging
import os
import time
from typing import Optional, Tuple

from tools.browser.vision.models import (
    ScreenshotCapture,
    VisualVerification,
    VisionConfig,
)

logger = logging.getLogger("VisualDiffer")


class VisualDiffer:
    """Compares before/after screenshots to verify browser action effects.

    Uses pixel-level comparison to detect changes and generate visual
    diff images. No external ML/CV dependencies — uses only Pillow.

    Architecture position:
        - Receives before/after ScreenshotCapture pairs
        - Outputs VisualVerification results with change metrics
        - Used by VisionPipeline for action outcome verification

    Attributes:
        config: Vision pipeline configuration.
    """

    def __init__(self, config: Optional[VisionConfig] = None) -> None:
        """Initialize the Visual Differ.

        Args:
            config: Vision pipeline configuration. Defaults to VisionConfig().
        """
        self.config = config or VisionConfig()
        self._logger = logger

    def compare(
        self,
        before: ScreenshotCapture,
        after: ScreenshotCapture,
        action_name: str = "",
    ) -> VisualVerification:
        """Compare two screenshots and produce a verification result.

        Args:
            before: Screenshot captured before the action.
            after: Screenshot captured after the action.
            action_name: Name of the action that was performed between captures.

        Returns:
            VisualVerification: Comparison result with change metrics.
        """
        verification = VisualVerification(
            action_name=action_name,
            before_capture=before,
            after_capture=after,
        )

        if not before.image_bytes or not after.image_bytes:
            verification.change_description = (
                "Cannot compare: one or both screenshots have no image data."
            )
            return verification

        try:
            from PIL import Image
        except ImportError:
            self._logger.warning("Pillow not available — skipping visual comparison.")
            verification.change_description = "Pillow not available for comparison."
            return verification

        try:
            before_img = Image.open(io.BytesIO(before.image_bytes)).convert("RGB")
            after_img = Image.open(io.BytesIO(after.image_bytes)).convert("RGB")

            # Resize to common dimensions if they differ
            if before_img.size != after_img.size:
                # Use the smaller dimensions for comparison
                common_w = min(before_img.width, after_img.width)
                common_h = min(before_img.height, after_img.height)
                before_img = before_img.resize((common_w, common_h), Image.LANCZOS)
                after_img = after_img.resize((common_w, common_h), Image.LANCZOS)

            # Pixel-by-pixel comparison
            change_pct, diff_img = self._pixel_diff(before_img, after_img)

            verification.change_percentage = change_pct
            verification.change_detected = change_pct >= self.config.diff_threshold

            # Generate human-readable description
            verification.change_description = self._describe_change(
                change_pct, before, after
            )

            # Save diff image to disk if configured
            if (
                verification.change_detected
                and diff_img is not None
                and self.config.save_captures_to_disk
            ):
                diff_path = self._save_diff_image(diff_img, action_name)
                verification.diff_file_path = diff_path

            self._logger.debug(
                f"Visual diff: {change_pct:.2f}% changed "
                f"(threshold: {self.config.diff_threshold}%), "
                f"change_detected: {verification.change_detected}"
            )

        except Exception as e:
            self._logger.error(f"Visual comparison failed: {e}")
            verification.change_description = f"Comparison error: {e}"

        return verification

    def _pixel_diff(
        self, before_img: "Image.Image", after_img: "Image.Image"
    ) -> Tuple[float, Optional["Image.Image"]]:
        """Compute pixel-level difference between two images.

        Args:
            before_img: PIL Image from before the action.
            after_img: PIL Image from after the action.

        Returns:
            Tuple of (change_percentage, diff_image).
            change_percentage is 0.0-100.0.
            diff_image is a PIL Image highlighting changed pixels in red.
        """
        from PIL import Image

        width, height = before_img.size
        total_pixels = width * height

        if total_pixels == 0:
            return 0.0, None

        before_pixels = before_img.load()
        after_pixels = after_img.load()

        # Create diff image (black background, changed pixels in color)
        diff_img = Image.new("RGB", (width, height), (0, 0, 0))
        diff_pixels = diff_img.load()

        changed_count = 0
        # Pixel difference threshold (per channel) to count as "changed"
        channel_threshold = 30

        for y in range(height):
            for x in range(width):
                r1, g1, b1 = before_pixels[x, y]
                r2, g2, b2 = after_pixels[x, y]

                dr = abs(r1 - r2)
                dg = abs(g1 - g2)
                db = abs(b1 - b2)

                if dr > channel_threshold or dg > channel_threshold or db > channel_threshold:
                    changed_count += 1
                    # Highlight changed pixels: red intensity proportional to change
                    intensity = min(255, (dr + dg + db))
                    diff_pixels[x, y] = (intensity, 50, 50)
                else:
                    # Show unchanged pixels as dim gray
                    diff_pixels[x, y] = (r2 // 4, g2 // 4, b2 // 4)

        change_pct = (changed_count / total_pixels) * 100.0
        return change_pct, diff_img

    def _describe_change(
        self,
        change_pct: float,
        before: ScreenshotCapture,
        after: ScreenshotCapture,
    ) -> str:
        """Generate a human-readable description of the visual change.

        Args:
            change_pct: Percentage of pixels that changed.
            before: Before screenshot metadata.
            after: After screenshot metadata.

        Returns:
            str: Description string.
        """
        if change_pct < 0.1:
            return "No significant visual change detected."
        elif change_pct < 1.0:
            return f"Minor visual change ({change_pct:.2f}% of pixels). Likely subtle UI update."
        elif change_pct < 10.0:
            return f"Moderate visual change ({change_pct:.1f}% of pixels). UI element state likely changed."
        elif change_pct < 50.0:
            return f"Significant visual change ({change_pct:.1f}% of pixels). Page content likely updated."
        else:
            url_changed = before.page_url != after.page_url
            if url_changed:
                return (
                    f"Major visual change ({change_pct:.1f}% of pixels). "
                    f"Navigation from '{before.page_url}' to '{after.page_url}'."
                )
            return f"Major visual change ({change_pct:.1f}% of pixels). Page substantially changed."

    def _save_diff_image(self, diff_img: "Image.Image", action_name: str) -> str:
        """Save the diff image to disk.

        Args:
            diff_img: PIL Image of the visual diff.
            action_name: Action name for the filename.

        Returns:
            str: Absolute path to the saved diff image, or empty string on failure.
        """
        directory = os.path.abspath(self.config.capture_directory)
        os.makedirs(directory, exist_ok=True)

        safe_action = action_name.replace(" ", "_").replace("/", "_")[:30]
        filename = f"diff_{safe_action}_{int(time.time())}.png"
        filepath = os.path.join(directory, filename)

        try:
            diff_img.save(filepath, format="PNG")
            self._logger.debug(f"Diff image saved: {filepath}")
            return filepath
        except Exception as e:
            self._logger.error(f"Failed to save diff image: {e}")
            return ""
