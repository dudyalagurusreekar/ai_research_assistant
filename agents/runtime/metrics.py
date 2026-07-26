import time
from typing import Dict, Any

class SafetyMetricsCollector:
    """
    Tracks operation telemetry for code safety checks, AST rewrites, execution outcomes,
    and processing times.
    """

    def __init__(self):
        self.validations_total = 0
        self.validation_failures = 0
        self.static_rewrites = 0
        self.execution_successes = 0
        self.execution_failures = 0
        self.llm_regenerations = 0
        self.total_safety_overhead_time = 0.0

    def increment_validations(self):
        self.validations_total += 1

    def increment_validation_failures(self):
        self.validation_failures += 1

    def increment_rewrites(self):
        self.static_rewrites += 1

    def increment_execution_successes(self):
        self.execution_successes += 1

    def increment_execution_failures(self):
        self.execution_failures += 1

    def increment_regenerations(self):
        self.llm_regenerations += 1

    def record_time(self, seconds: float):
        self.total_safety_overhead_time += seconds

    def get_report(self) -> Dict[str, Any]:
        """Compiles a readable metrics report dictionary."""
        return {
            "validations_total": self.validations_total,
            "validation_failures": self.validation_failures,
            "static_rewrites": self.static_rewrites,
            "execution_successes": self.execution_successes,
            "execution_failures": self.execution_failures,
            "llm_regenerations": self.llm_regenerations,
            "total_safety_overhead_seconds": round(self.total_safety_overhead_time, 4)
        }
