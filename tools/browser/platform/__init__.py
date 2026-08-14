"""Sprint 11 Browser Automation Platform Package."""

from tools.browser.platform.models import (
    BrowserConfig,
    SessionConfig,
    DOMNode,
    DOMTree,
    BrowserAction,
    ActionResult,
    ActionType,
    WaitStrategy,
    ExtractionSchema,
    ExtractionResult,
    CaptchaDetectionResult,
    SecurityAssessmentResult,
    WorkflowStep,
    WorkflowDefinition,
    WorkflowExecutionResult,
    BrowserMetrics,
)
from tools.browser.platform.browser_manager import BrowserManager
from tools.browser.platform.session_manager import SessionManager
from tools.browser.platform.navigation_engine import NavigationEngine
from tools.browser.platform.dom_engine import DOMUnderstandingEngine
from tools.browser.platform.interaction_engine import InteractionEngine
from tools.browser.platform.extraction_engine import ExtractionEngine
from tools.browser.platform.auth_manager import AuthenticationManager
from tools.browser.platform.download_manager import DownloadManager
from tools.browser.platform.upload_manager import UploadManager
from tools.browser.platform.screenshot_manager import ScreenshotManager
from tools.browser.platform.captcha_detector import CaptchaDetector
from tools.browser.platform.workflow_recorder import WorkflowRecorder
from tools.browser.platform.workflow_executor import WorkflowExecutor
from tools.browser.platform.error_recovery import ErrorRecoveryEngine
from tools.browser.platform.security_layer import SecurityLayer
from tools.browser.platform.metrics import BrowserMetricsEngine
from tools.browser.platform.engine import BrowserPlatformEngine

__all__ = [
    "BrowserConfig",
    "SessionConfig",
    "DOMNode",
    "DOMTree",
    "BrowserAction",
    "ActionResult",
    "ActionType",
    "WaitStrategy",
    "ExtractionSchema",
    "ExtractionResult",
    "CaptchaDetectionResult",
    "SecurityAssessmentResult",
    "WorkflowStep",
    "WorkflowDefinition",
    "WorkflowExecutionResult",
    "BrowserMetrics",
    "BrowserManager",
    "SessionManager",
    "NavigationEngine",
    "DOMUnderstandingEngine",
    "InteractionEngine",
    "ExtractionEngine",
    "AuthenticationManager",
    "DownloadManager",
    "UploadManager",
    "ScreenshotManager",
    "CaptchaDetector",
    "WorkflowRecorder",
    "WorkflowExecutor",
    "ErrorRecoveryEngine",
    "SecurityLayer",
    "BrowserMetricsEngine",
    "BrowserPlatformEngine",
]
