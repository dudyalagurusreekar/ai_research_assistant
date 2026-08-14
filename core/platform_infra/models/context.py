"""Platform Context model — Enterprise Platform Session state container."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.platform_infra.models.auth import AuthContext, UserIdentity
from core.platform_infra.models.observability import TraceContext


@dataclass
class PlatformContext:
    """Enterprise Platform Session Context."""

    session_id: str = field(default_factory=lambda: f"plt_{uuid.uuid4().hex[:8]}")
    tenant_id: str = "default_tenant"
    auth_ctx: Optional[AuthContext] = None
    trace_ctx: TraceContext = field(default_factory=TraceContext)
    active_environment: str = "production"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "user_id": self.auth_ctx.user.user_id if self.auth_ctx else "anonymous",
            "trace_id": self.trace_ctx.trace_id,
            "environment": self.active_environment,
        }
