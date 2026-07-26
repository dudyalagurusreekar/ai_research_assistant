"""Browser Tool Package for AI Research Assistant.

This package provides a clean, modular, production-quality Browser Tool.

Package Architecture:
- `constants`: Enums, status codes, default configuration settings.
- `exceptions`: Custom error hierarchy for browser errors.
- `types`: Type aliases, Protocols, interfaces.
- `config`: `BrowserConfig` configuration manager.
- `models`: DTOs for `BrowserRequest`, `BrowserResponse`, `PageState`, `PageMetadata`.
- `utils`: Helpers for URL validation, sanitization, logging.
- `core`: Abstract interfaces (`BaseFetcher`, `BaseParser`) and `Browser` orchestrator.
- `session`: Session Orchestrator for lifecycle management and multi-goal coordination.
- `vision`: Vision Pipeline for screenshot capture, annotation, and visual verification.
- `tabs`: Multi-Tab Coordinator for tab lifecycle, switching, and cross-tab operations.
- `tool`: `BrowserTool` smolagents wrapper.
"""

from tools.browser.constants import (
    HttpMethod,
    BrowserAction,
    PageStatus,
    BrowserEngineType,
)
from tools.browser.exceptions import (
    BrowserError,
    ConfigurationError,
    ValidationError,
    NavigationError,
    FetchError,
    ParsingError,
)
from tools.browser.config import BrowserConfig
from tools.browser.models import (
    BrowserRequest,
    NavigationParams,
    ActionParams,
    BrowserResponse,
    PageMetadata,
    PerformanceMetrics,
    FetchResult,
    ActionResult,
    ActionMetrics,
    PageState,
    ElementNode,
    LinkInfo,
    FormInfo,
)
from tools.browser.fetchers.http_fetcher import HTTPFetcher
from tools.browser.fetchers.playwright_fetcher import PlaywrightFetcher
from tools.browser.fetchers.factory import FetcherFactory
from tools.browser.automation import (
    BrowserAutomationEngine,
    PlaywrightStrategy,
    AutomationStrategyFactory,
    AutomationStrategy,
    AutomationError,
    ElementNotFoundError,
    InteractionError,
    SessionState,
    NetworkObserver,
)
from tools.browser.parsers import (
    HTMLCleaner,
    BS4Parser,
    ParserFactory,
)
from tools.browser.services import (
    ContentRouter,
    LanguageDetector,
)
from tools.browser.crawler import (
    CrawlNode,
    CrawlStats,
    CrawlResult,
    TraversalStrategy,
    BFSTraversal,
    DFSTraversal,
    RobotsTxtHandler,
    SitemapParser,
    CrawlerEngine,
)
from tools.browser.core import (
    BaseFetcher,
    BaseParser,
    Browser,
)
from tools.browser.executor import BrowserActionExecutor
from tools.browser.planner.engine import TaskPlannerEngine
from tools.browser.state_manager import BrowserStateSnapshot, BrowserStateMemoryManager
from tools.browser.recovery import RecoveryEngine, ErrorCategory, ErrorClassifier
from tools.browser.session import (
    SessionOrchestrator,
    SessionConfig,
    SessionMetadata,
    SessionState as BrowserSessionState,
    GoalResult,
    SessionError,
    SessionHook,
    LoggingHook,
    MetricsHook,
    SessionPersistence,
)
from tools.browser.vision import (
    VisionPipeline,
    VisionConfig,
    ScreenshotManager,
    DOMAnnotator,
    VisualDiffer,
    ScreenshotCapture,
    VisualElement,
    VisualVerification,
    BoundingBox,
    ElementType,
    AnnotationMode,
)
from tools.browser.tabs import (
    MultiTabCoordinator,
    TabInfo,
    TabGroup,
    TabEvent,
    TabEventRecord,
    TabStrategy,
    ConservativeStrategy,
    ParallelStrategy,
    TabLimitExceeded,
    TabNotFoundError,
)
from tools.browser.detector import (
    CompletionDetector,
    CompletionState,
    CompletionStatus,
    CompletionContext,
    BaseCompletionStrategy,
)
from tools.browser.loop import (
    LoopDetector,
    LoopType,
    LoopDetectionResult,
    LoopDetectorError,
)
from tools.browser.budget import (
    BudgetManager,
    ResourceCategory,
    BudgetStatus,
    BudgetRecommendation,
    BudgetLimit,
    BudgetExceededError,
)
from tools.browser.compressor import (
    PromptCompressor,
    CompressedContext,
    CompressionStrategyType,
    BaseCompressorStrategy,
)
from tools.browser.reporting import (
    ReportingEngine,
    ReportFormat,
    ReportMetadata,
    ReportData,
    ReportingError,
)
from tools.browser.tool import BrowserTool

__all__ = [
    # Enums
    "HttpMethod",
    "BrowserAction",
    "PageStatus",
    "BrowserEngineType",
    # Exceptions
    "BrowserError",
    "ConfigurationError",
    "ValidationError",
    "NavigationError",
    "FetchError",
    "ParsingError",
    "AutomationError",
    "ElementNotFoundError",
    "InteractionError",
    # Config
    "BrowserConfig",
    # Models
    "BrowserRequest",
    "NavigationParams",
    "ActionParams",
    "BrowserResponse",
    "PageMetadata",
    "PerformanceMetrics",
    "FetchResult",
    "ActionResult",
    "ActionMetrics",
    "PageState",
    "ElementNode",
    "LinkInfo",
    "FormInfo",
    "SessionState",
    # Crawler DTOs
    "CrawlNode",
    "CrawlStats",
    "CrawlResult",
    "TraversalStrategy",
    "BFSTraversal",
    "DFSTraversal",
    "RobotsTxtHandler",
    "SitemapParser",
    # Automation
    "BrowserAutomationEngine",
    "AutomationStrategy",
    "PlaywrightStrategy",
    "AutomationStrategyFactory",
    "NetworkObserver",
    # Fetchers, Parsers, Services & Interfaces
    "BaseFetcher",
    "HTTPFetcher",
    "PlaywrightFetcher",
    "FetcherFactory",
    "BaseParser",
    "HTMLCleaner",
    "BS4Parser",
    "ParserFactory",
    "ContentRouter",
    "LanguageDetector",
    "CrawlerEngine",
    "Browser",
    # Executor
    "BrowserActionExecutor",
    # Task Planner Engine
    "TaskPlannerEngine",
    # State Manager
    "BrowserStateSnapshot",
    "BrowserStateMemoryManager",
    # Recovery Engine
    "RecoveryEngine",
    "ErrorCategory",
    "ErrorClassifier",
    # Agent Tool
    "BrowserTool",
    # Session Orchestrator
    "SessionOrchestrator",
    "SessionConfig",
    "SessionMetadata",
    "BrowserSessionState",
    "GoalResult",
    "SessionError",
    "SessionHook",
    "LoggingHook",
    "MetricsHook",
    "SessionPersistence",
    # Vision Pipeline
    "VisionPipeline",
    "VisionConfig",
    "ScreenshotManager",
    "DOMAnnotator",
    "VisualDiffer",
    "ScreenshotCapture",
    "VisualElement",
    "VisualVerification",
    "BoundingBox",
    "ElementType",
    "AnnotationMode",
    # Multi-Tab Coordinator
    "MultiTabCoordinator",
    "TabInfo",
    "TabGroup",
    "TabEvent",
    "TabEventRecord",
    "TabStrategy",
    "ConservativeStrategy",
    "ParallelStrategy",
    "TabLimitExceeded",
    "TabNotFoundError",
    # Completion Detector
    "CompletionDetector",
    "CompletionState",
    "CompletionStatus",
    "CompletionContext",
    "BaseCompletionStrategy",
    # Loop Detector
    "LoopDetector",
    "LoopType",
    "LoopDetectionResult",
    "LoopDetectorError",
    # Budget Manager
    "BudgetManager",
    "ResourceCategory",
    "BudgetStatus",
    "BudgetRecommendation",
    "BudgetLimit",
    "BudgetExceededError",
    # Prompt Compressor
    "PromptCompressor",
    "CompressedContext",
    "CompressionStrategyType",
    "BaseCompressorStrategy",
    # Reporting Engine
    "ReportingEngine",
    "ReportFormat",
    "ReportMetadata",
    "ReportData",
    "ReportingError",
]
