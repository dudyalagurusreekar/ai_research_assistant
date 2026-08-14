"""AdaptiveToolRegistry — enriched capability store for ARA v2.0.

Maintains ToolCapabilityDescriptors for all tools registered platform-wide,
tracks historical reliability (0.0 to 1.0), updates average latency, manages tool health
states, and provides intelligent tool lookup matching tasks to optimal capabilities.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.execution.models.descriptor import ToolCapabilityDescriptor, ToolHealthStatus
from infrastructure.logging.logger import StructuredLogger

# Default specifications for standard platform tools
DEFAULT_DESCRIPTORS: Dict[str, Dict[str, Any]] = {
    "search_tool": {
        "description": "Deep web & academic database search engine",
        "capabilities": ["search", "web_search", "academic_search"],
        "task_types": ["factual_qa", "multi_step_research", "comparison"],
        "estimated_latency_ms": 1500.0,
        "cost_per_call": 0.002,
        "reliability_score": 0.98,
        "fallback_tools": ["browser_tool", "python_interpreter"],
    },
    "browser_tool": {
        "description": "Autonomous browser navigation and DOM parsing",
        "capabilities": ["browse", "web_browsing", "scrape"],
        "task_types": ["multi_step_research", "web_browsing"],
        "estimated_latency_ms": 3500.0,
        "cost_per_call": 0.005,
        "reliability_score": 0.92,
        "fallback_tools": ["search_tool", "python_interpreter"],
    },
    "document_tool": {
        "description": "PDF/DOCX/HTML ingestion, chunking, and entity parsing",
        "capabilities": ["document", "pdf_parse", "file_read"],
        "task_types": ["document_analysis", "report_generation"],
        "estimated_latency_ms": 2500.0,
        "cost_per_call": 0.003,
        "reliability_score": 0.95,
        "fallback_tools": ["python_interpreter"],
    },
    "code_tool": {
        "description": "Secure Python sandbox execution environment",
        "capabilities": ["code", "python_exec", "sandbox"],
        "task_types": ["code_execution", "data_analysis"],
        "estimated_latency_ms": 800.0,
        "cost_per_call": 0.001,
        "reliability_score": 0.99,
        "fallback_tools": ["python_interpreter"],
    },
    "memory_tool": {
        "description": "RAG vector memory store and recall graph",
        "capabilities": ["memory", "vector_store", "recall"],
        "task_types": ["memory_operation"],
        "estimated_latency_ms": 200.0,
        "cost_per_call": 0.0005,
        "reliability_score": 0.99,
        "fallback_tools": ["python_interpreter"],
    },
    "vision_tool": {
        "description": "Multi-modal vision and OCR image analysis",
        "capabilities": ["vision", "ocr", "chart_analysis"],
        "task_types": ["vision_analysis"],
        "estimated_latency_ms": 2000.0,
        "cost_per_call": 0.008,
        "reliability_score": 0.94,
        "fallback_tools": ["python_interpreter"],
    },
    "report_tool": {
        "description": "Report structure generator and validator",
        "capabilities": ["report", "validate", "format"],
        "task_types": ["report_generation"],
        "estimated_latency_ms": 500.0,
        "cost_per_call": 0.001,
        "reliability_score": 0.98,
        "fallback_tools": ["python_interpreter"],
    },
    "python_interpreter": {
        "description": "Core orchestration and synthesis python runtime",
        "capabilities": ["python", "orchestrate", "synthesize"],
        "task_types": ["general_qa", "comparison", "data_analysis"],
        "estimated_latency_ms": 100.0,
        "cost_per_call": 0.0,
        "reliability_score": 1.0,
        "fallback_tools": [],
    },
}


class AdaptiveToolRegistry:
    """Central manager for tool capability descriptors and dynamic reliability metrics."""

    def __init__(self) -> None:
        self._descriptors: Dict[str, ToolCapabilityDescriptor] = {}
        self._logger = StructuredLogger("AdaptiveToolRegistry")
        self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        """Populate the registry with standard platform descriptors."""
        for name, spec in DEFAULT_DESCRIPTORS.items():
            descriptor = ToolCapabilityDescriptor(
                name=name,
                description=spec["description"],
                capabilities=spec["capabilities"],
                task_types=spec["task_types"],
                estimated_latency_ms=spec["estimated_latency_ms"],
                avg_actual_latency_ms=spec["estimated_latency_ms"],
                cost_per_call=spec["cost_per_call"],
                reliability_score=spec["reliability_score"],
                fallback_tools=spec["fallback_tools"],
            )
            self._descriptors[name] = descriptor

    def register_descriptor(self, descriptor: ToolCapabilityDescriptor) -> None:
        """Register or overwrite a tool capability descriptor."""
        self._descriptors[descriptor.name] = descriptor
        self._logger.info(f"Registered capability descriptor for '{descriptor.name}'")

    def register_from_tool_info(self, tool_info: Dict[str, Any]) -> ToolCapabilityDescriptor:
        """Register or update a descriptor from raw tool info dict."""
        name = tool_info.get("name", "")
        if not name:
            raise ValueError("Tool info must include 'name'")

        if name in self._descriptors:
            return self._descriptors[name]

        # Use defaults if available, else derive from tool_info
        defaults = DEFAULT_DESCRIPTORS.get(name, {})
        descriptor = ToolCapabilityDescriptor(
            name=name,
            description=tool_info.get("description") or defaults.get("description", ""),
            capabilities=tool_info.get("capabilities") or defaults.get("capabilities", [name]),
            task_types=defaults.get("task_types", ["general"]),
            estimated_latency_ms=defaults.get("estimated_latency_ms", 1000.0),
            avg_actual_latency_ms=defaults.get("estimated_latency_ms", 1000.0),
            cost_per_call=defaults.get("cost_per_call", 0.001),
            reliability_score=defaults.get("reliability_score", 0.95),
            fallback_tools=defaults.get("fallback_tools", ["python_interpreter"]),
        )
        self._descriptors[name] = descriptor
        return descriptor

    def get_descriptor(self, name: str) -> Optional[ToolCapabilityDescriptor]:
        """Retrieve a descriptor by tool name."""
        return self._descriptors.get(name)

    def list_descriptors(self) -> List[ToolCapabilityDescriptor]:
        """Return all registered descriptors."""
        return list(self._descriptors.values())

    def list_healthy_descriptors(self) -> List[ToolCapabilityDescriptor]:
        """Return descriptors for healthy and degraded (available) tools."""
        return [d for d in self._descriptors.values() if d.is_available()]

    def find_by_capability(self, capability: str) -> List[ToolCapabilityDescriptor]:
        """Find descriptors matching a capability string (case-insensitive)."""
        cap_lower = capability.lower().strip()
        matched: List[ToolCapabilityDescriptor] = []
        for d in self.list_healthy_descriptors():
            caps = [c.lower() for c in d.capabilities]
            if cap_lower in caps or cap_lower == d.name.lower():
                matched.append(d)
        return matched

    def record_outcome(self, tool_name: str, success: bool, latency_ms: float = 0.0, error_message: str = "") -> None:
        """Update dynamic reliability metrics and health status following an execution."""
        d = self._descriptors.get(tool_name)
        if not d:
            return

        if success:
            d.record_success(latency_ms)
            self._logger.debug(
                f"Tool '{tool_name}' success recorded: reliability={d.reliability_score:.2f}, "
                f"avg_latency={d.avg_actual_latency_ms:.1f}ms"
            )
        else:
            d.record_failure(error_message)
            self._logger.warning(
                f"Tool '{tool_name}' failure recorded: reliability={d.reliability_score:.2f}, "
                f"consecutive_failures={d.consecutive_failures}, health={d.health_status.value}"
            )

    def reset_health(self, tool_name: Optional[str] = None) -> None:
        """Reset consecutive failures and restore tool health status."""
        if tool_name:
            d = self._descriptors.get(tool_name)
            if d:
                d.consecutive_failures = 0
                d.health_status = ToolHealthStatus.HEALTHY
                d.reliability_score = max(d.reliability_score, 0.90)
        else:
            for d in self._descriptors.values():
                d.consecutive_failures = 0
                d.health_status = ToolHealthStatus.HEALTHY
                d.reliability_score = max(d.reliability_score, 0.90)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entire registry state for telemetry."""
        return {
            "total_tools": len(self._descriptors),
            "healthy_tools": len(self.list_healthy_descriptors()),
            "descriptors": {name: d.to_dict() for name, d in self._descriptors.items()},
        }
