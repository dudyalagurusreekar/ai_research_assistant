"""Base classes, enums, DTOs, and exception types for execution loop detection.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class LoopDetectorError(Exception):
    """Base exception for all loop detection errors."""


class LoopType(str, Enum):
    """Represents the type of loop detected in browser automation."""

    NAVIGATION = "NAVIGATION"      # Cycle of visited URLs (e.g. A -> B -> A)
    ACTION = "ACTION"              # Cycle of identical actions, selectors, and inputs
    STATE = "STATE"                # Oscillation between matching page layout hashes
    RECOVERY = "RECOVERY"          # Cyclic retry/recovery attempts on the same selector
    PLANNER = "PLANNER"            # Repeating reasoning/decision thoughts from the planner


@dataclass
class LoopDetectionResult:
    """Consolidated outcome of the loop detection check.

    Attributes:
        loop_detected: True if a loop has been flagged.
        loop_type: The identified LoopType, if any.
        confidence: Normalised confidence score from 0.0 to 1.0.
        explanation: Natural language justification explaining the loop signature.
        cycle_length: Number of actions/states in the repeating loop cycle.
        recommended_escape: Suggested escape strategy (replan, rollback, skip, terminate).
        details: Metadata diagnostic properties.
    """

    loop_detected: bool
    loop_type: Optional[LoopType] = None
    confidence: float = 0.0
    explanation: str = ""
    cycle_length: int = 0
    recommended_escape: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert loop detection result to dictionary."""
        return {
            "loop_detected": self.loop_detected,
            "loop_type": self.loop_type.value if self.loop_type else None,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "cycle_length": self.cycle_length,
            "recommended_escape": self.recommended_escape,
            "details": self.details,
        }
