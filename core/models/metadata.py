"""Tool metadata model."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ToolMetadata:
    """Metadata definition for tools and capabilities registered platform-wide."""

    name: str
    version: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    parameters_schema: Dict[str, Any] = field(default_factory=dict)
    returns_schema: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    is_async: bool = True
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize metadata to dictionary representation."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "capabilities": self.capabilities,
            "parameters_schema": self.parameters_schema,
            "returns_schema": self.returns_schema,
            "tags": self.tags,
            "is_async": self.is_async,
            "enabled": self.enabled,
        }
