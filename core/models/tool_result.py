"""Tool execution result model."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from core.models.artifact import Artifact


@dataclass
class ToolResult:
    """Encapsulates the output and performance metrics of a tool execution."""

    tool_name: str
    success: bool
    data: Optional[Any] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    artifacts: List[Artifact] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize ToolResult to dictionary representation."""
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "data": self.data,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
            "artifacts": [art.to_dict() for art in self.artifacts],
            "metadata": self.metadata,
        }
