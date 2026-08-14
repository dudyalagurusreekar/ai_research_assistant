"""Plugin models — Extension SDK manifests and hook registration models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class PluginStatus(Enum):
    """Plugin status lifecycle states."""

    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    FAILED = "failed"


class PluginHookType(Enum):
    """Event hook points across platform execution pipeline."""

    PRE_PLANNING = "pre_planning"
    POST_PLANNING = "post_planning"
    PRE_EXECUTION = "pre_execution"
    POST_EXECUTION = "post_execution"
    ON_ERROR = "on_error"


@dataclass
class PluginManifest:
    """Plugin definition manifest."""

    plugin_id: str
    name: str
    version: str = "1.0.0"
    author: str = "Community"
    description: str = ""
    entry_point: str = "plugin.main"
    hooks: List[PluginHookType] = field(default_factory=list)
    status: PluginStatus = PluginStatus.INSTALLED
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "status": self.status.value,
            "hooks": [h.value for h in self.hooks],
        }
