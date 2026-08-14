"""Release Gate Configuration and Verdict Models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class GateStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


@dataclass
class ReleaseGateConfig:
    """Mandatory quality gate thresholds defined for Sprint 14 ARA releases."""

    min_overall_success_rate: float = 95.0  # >= 95%
    min_citation_accuracy: float = 98.0  # >= 98%
    max_hallucination_rate: float = 2.0  # <= 2%
    min_planner_accuracy: float = 95.0  # >= 95%
    min_tool_selection_accuracy: float = 95.0  # >= 95%
    min_browser_automation_success: float = 95.0  # >= 95%
    min_connector_success: float = 95.0  # >= 95%
    min_reflection_success: float = 90.0  # >= 90%
    min_recovery_success: float = 95.0  # >= 95%
    min_security_pass_rate: float = 100.0  # 100% Pass
    max_regression_failures: int = 0  # 0 regressions allowed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_overall_success_rate": self.min_overall_success_rate,
            "min_citation_accuracy": self.min_citation_accuracy,
            "max_hallucination_rate": self.max_hallucination_rate,
            "min_planner_accuracy": self.min_planner_accuracy,
            "min_tool_selection_accuracy": self.min_tool_selection_accuracy,
            "min_browser_automation_success": self.min_browser_automation_success,
            "min_connector_success": self.min_connector_success,
            "min_reflection_success": self.min_reflection_success,
            "min_recovery_success": self.min_recovery_success,
            "min_security_pass_rate": self.min_security_pass_rate,
            "max_regression_failures": self.max_regression_failures,
        }


@dataclass
class GateCheckResult:
    """Individual gate threshold evaluation item."""

    gate_name: str = ""
    target_value: float = 0.0
    actual_value: float = 0.0
    passed: bool = True
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "target_value": self.target_value,
            "actual_value": self.actual_value,
            "passed": self.passed,
            "message": self.message,
        }


@dataclass
class ReleaseGateVerdict:
    """Final release verdict determining whether a build can proceed to production."""

    verdict_id: str = field(default_factory=lambda: f"verdict_{uuid.uuid4().hex[:8]}")
    status: GateStatus = GateStatus.PASSED
    release_approved: bool = True
    gate_checks: List[GateCheckResult] = field(default_factory=list)
    failed_gate_count: int = 0
    verdict_summary: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict_id": self.verdict_id,
            "status": self.status.value,
            "release_approved": self.release_approved,
            "gate_checks": [gc.to_dict() for gc in self.gate_checks],
            "failed_gate_count": self.failed_gate_count,
            "verdict_summary": self.verdict_summary,
            "timestamp": self.timestamp.isoformat(),
        }
