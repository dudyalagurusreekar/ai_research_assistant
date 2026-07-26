"""Loop Detector Package.

Exposes the main orchestrator, types, and custom exceptions.
"""

from tools.browser.loop.base import LoopDetectionResult, LoopDetectorError, LoopType
from tools.browser.loop.detector import LoopDetector
from tools.browser.loop.fingerprint import BrowserStateFingerprinter

__all__ = [
    "LoopDetector",
    "LoopType",
    "LoopDetectionResult",
    "LoopDetectorError",
    "BrowserStateFingerprinter",
]
