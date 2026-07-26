"""Browser State model tracking tabs, cookies, history, downloads, uploads, and DOM versions."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from core.utils.time_utils import utc_now


@dataclass
class TabInfo:
    """Tab descriptor model."""

    tab_id: str
    url: str
    title: str = ""
    is_active: bool = True


@dataclass
class DownloadRecord:
    """Download record model."""

    file_path: str
    origin_url: str
    size_bytes: int = 0
    timestamp: datetime = field(default_factory=utc_now)


@dataclass
class BrowserStateModel:
    """Encapsulates the complete snapshot state of the browser capability."""

    url: str = "about:blank"
    active_tab_id: str = "tab_1"
    tabs: Dict[str, TabInfo] = field(default_factory=lambda: {"tab_1": TabInfo("tab_1", "about:blank")})
    cookies: Dict[str, str] = field(default_factory=dict)
    history: List[str] = field(default_factory=list)
    downloads: List[DownloadRecord] = field(default_factory=list)
    uploads: List[str] = field(default_factory=list)
    dom_version_hash: str = ""
    scroll_x: int = 0
    scroll_y: int = 0
    updated_at: datetime = field(default_factory=utc_now)

    def record_navigation(self, new_url: str, dom_hash: str = "") -> None:
        """Update active state on navigation."""
        self.url = new_url
        if not self.history or self.history[-1] != new_url:
            self.history.append(new_url)
        self.dom_version_hash = dom_hash
        self.updated_at = utc_now()
        if self.active_tab_id in self.tabs:
            self.tabs[self.active_tab_id].url = new_url

    def to_dict(self) -> Dict[str, Any]:
        """Serialize browser state to dictionary representation."""
        return {
            "url": self.url,
            "active_tab_id": self.active_tab_id,
            "tabs": {k: {"url": v.url, "title": v.title} for k, v in self.tabs.items()},
            "history": self.history,
            "downloads": [d.file_path for d in self.downloads],
            "uploads": self.uploads,
            "dom_version_hash": self.dom_version_hash,
            "scroll_position": {"x": self.scroll_x, "y": self.scroll_y},
            "updated_at": self.updated_at.isoformat(),
        }
