"""Pydantic data models for Browser Automation Platform."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BrowserSessionConfig(BaseModel):
    session_id: str
    user_id: str
    browser_type: str = "chromium"  # chromium, firefox, webkit
    headless: bool = True
    user_agent: Optional[str] = None
    viewport_width: int = 1280
    viewport_height: int = 800
    proxy_url: Optional[str] = None
    storage_state_path: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PageMetadata(BaseModel):
    url: str
    title: str
    status_code: int = 200
    meta_description: Optional[str] = None
    links_count: int = 0
    images_count: int = 0
    loaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DOMElementNode(BaseModel):
    tag_name: str
    id: Optional[str] = None
    class_name: Optional[str] = None
    role: Optional[str] = None
    text_content: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)
    is_interactive: bool = False
    xpath: Optional[str] = None
    selector: Optional[str] = None


class ExtractionResult(BaseModel):
    url: str
    extracted_text: str
    tables: List[List[List[str]]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    links: List[Dict[str, str]] = Field(default_factory=list)
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BrowserDownload(BaseModel):
    download_id: str
    session_id: str
    filename: str
    url: str
    mime_type: str
    file_size: int
    storage_path: str
    rag_document_id: Optional[str] = None
    downloaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkflowStep(BaseModel):
    step_id: str
    action_type: str  # NAVIGATE, CLICK, TYPE, EXTRACT, DOWNLOAD, SCREENSHOT
    selector: Optional[str] = None
    value: Optional[str] = None
    target_url: Optional[str] = None
    description: Optional[str] = None
    timeout_ms: int = 30000
    require_confirmation: bool = False


class WorkflowDefinition(BaseModel):
    workflow_id: str
    name: str
    description: Optional[str] = None
    steps: List[WorkflowStep]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
