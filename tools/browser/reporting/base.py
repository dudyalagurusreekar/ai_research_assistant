"""Base classes, enums, DTOs, and exception types for execution reporting.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ReportingError(Exception):
    """Base exception for all Reporting Engine errors."""
    pass


class ReportFormat(str, Enum):
    """Supported output formats for execution reports."""

    JSON = "JSON"
    MARKDOWN = "MARKDOWN"
    HTML = "HTML"


@dataclass
class ExecutionEvent:
    """Represents a specific event captured during execution.

    Attributes:
        timestamp: Epoch timestamp of the event.
        step_number: Reasoning step index when event occurred.
        category: Event category (e.g. PLANNING, ACTION, RECOVERY, LOOP, COMPRESSION).
        message: Explanatory text description.
        metadata: Optional metadata attributes.
    """

    timestamp: float
    step_number: int
    category: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportMetadata:
    """High-level summary of the execution session.

    Attributes:
        objective: The target goal description.
        status: The final completion state string (e.g., COMPLETED, FAILED).
        duration_seconds: Cumulative run time.
        start_time: Epoch start time.
        end_time: Epoch completion time.
        confidence: Success confidence rating (0.0 to 1.0).
    """

    objective: str
    status: str
    duration_seconds: float
    start_time: float
    end_time: float
    confidence: float = 1.0


@dataclass
class ReportData:
    """Aggregated bundle of all logged events, artifacts, and resource metrics.

    Attributes:
        metadata: The session ReportMetadata DTO.
        timeline: Order-preserved list of ExecutionEvent objects.
        artifacts: Dictionary mapping artifact files or variables.
        recovery_statistics: Dictionary mapping healing counts and strategies.
        budget_utilization: Dictionary containing consumed resources summaries.
        details: Optional custom metadata mapping.
    """

    metadata: ReportMetadata
    timeline: List[ExecutionEvent] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    recovery_statistics: Dict[str, Any] = field(default_factory=dict)
    budget_utilization: Dict[str, Any] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)
