"""Strongly typed data models for Sprint 11 Browser Automation Platform."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import time


class ActionType(str, Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    HOVER = "hover"
    TYPE = "type"
    PRESS_KEY = "press_key"
    SCROLL = "scroll"
    SELECT_OPTION = "select_option"
    CLEAR = "clear"
    WAIT_FOR_SELECTOR = "wait_for_selector"
    WAIT_FOR_NAVIGATION = "wait_for_navigation"
    EXTRACT_TEXT = "extract_text"
    EXTRACT_TABLE = "extract_table"
    EXTRACT_SCHEMA = "extract_schema"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    SCREENSHOT = "screenshot"
    SWITCH_TAB = "switch_tab"
    CLOSE_TAB = "close_tab"


class WaitStrategy(str, Enum):
    DOM_CONTENT_LOADED = "domcontentloaded"
    LOAD = "load"
    NETWORK_IDLE = "networkidle"
    SELECTOR = "selector"


@dataclass
class BrowserConfig:
    headless: bool = True
    browser_type: str = "chromium"  # chromium, firefox, webkit
    viewport_width: int = 1280
    viewport_height: int = 800
    user_agent: Optional[str] = None
    timeout_ms: int = 30000
    slow_mo_ms: int = 0
    accept_downloads: bool = True
    proxy_url: Optional[str] = None
    max_contexts: int = 10
    debug_mode: bool = False


@dataclass
class SessionConfig:
    session_id: str
    cookies: List[Dict[str, Any]] = field(default_factory=list)
    local_storage: Dict[str, str] = field(default_factory=dict)
    session_storage: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class DOMNode:
    node_id: int
    tag_name: str
    text_content: str = ""
    attributes: Dict[str, str] = field(default_factory=dict)
    selector: str = ""
    xpath: str = ""
    is_interactive: bool = False
    is_visible: bool = True
    role: Optional[str] = None
    bounding_box: Optional[Dict[str, float]] = None
    children: List["DOMNode"] = field(default_factory=list)


@dataclass
class DOMTree:
    url: str
    title: str
    nodes: List[DOMNode] = field(default_factory=list)
    interactive_elements: List[DOMNode] = field(default_factory=list)
    accessibility_tree: Dict[str, Any] = field(default_factory=dict)
    simplified_html: str = ""
    total_nodes: int = 0


@dataclass
class BrowserAction:
    action_type: ActionType
    target_selector: Optional[str] = None
    url: Optional[str] = None
    text: Optional[str] = None
    value: Optional[str] = None
    file_path: Optional[str] = None
    key_name: Optional[str] = None
    scroll_direction: str = "down"
    scroll_amount: int = 500
    wait_strategy: WaitStrategy = WaitStrategy.NETWORK_IDLE
    timeout_ms: int = 15000
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionResult:
    success: bool
    action_type: ActionType
    message: str = ""
    url: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    screenshot_path: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0


@dataclass
class ExtractionSchema:
    schema_id: str
    name: str
    fields: Dict[str, str]  # field_name -> css_selector or json path
    container_selector: Optional[str] = None
    multiple: bool = False


@dataclass
class ExtractionResult:
    schema_id: str
    success: bool
    extracted_data: Union[Dict[str, Any], List[Dict[str, Any]]]
    item_count: int = 0
    extraction_time_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class CaptchaDetectionResult:
    captcha_detected: bool
    provider: Optional[str] = None  # recaptcha, hcaptcha, turnstile, geetest, bot_block
    confidence: float = 0.0
    details: str = ""


@dataclass
class SecurityAssessmentResult:
    is_safe: bool
    is_high_impact: bool
    requires_user_confirmation: bool
    risk_level: str = "low"  # low, medium, high, critical
    reasons: List[str] = field(default_factory=list)


@dataclass
class WorkflowStep:
    step_id: str
    description: str
    action: BrowserAction
    assertion: Optional[Dict[str, Any]] = None
    continue_on_failure: bool = False


@dataclass
class WorkflowDefinition:
    workflow_id: str
    name: str
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    input_parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class WorkflowExecutionResult:
    workflow_id: str
    success: bool
    step_results: List[ActionResult] = field(default_factory=list)
    execution_time_ms: float = 0.0
    failed_step_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class BrowserMetrics:
    total_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    total_navigations: int = 0
    captchas_detected: int = 0
    security_interceptions: int = 0
    total_execution_time_ms: float = 0.0
    average_action_latency_ms: float = 0.0
    active_contexts: int = 0
