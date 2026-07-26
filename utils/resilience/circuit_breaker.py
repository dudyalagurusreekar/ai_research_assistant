"""Circuit breaker and health tracking for LLM providers."""

import time
import logging
from typing import Dict, List

logger = logging.getLogger("LLMResilience.CircuitBreaker")


class ModelHealth:
    """Tracks state and latency metrics for a specific model provider."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.consecutive_failures = 0
        self.latencies: List[float] = []
        self.last_failure_time = 0.0
        self.status = "HEALTHY"  # HEALTHY, OPEN, HALF_OPEN
        self.open_until = 0.0

    @property
    def average_latency(self) -> float:
        """Calculates average latency of recent successful requests."""
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)

    def record_latency(self, latency: float) -> None:
        """Appends a new request latency to history, keeping the last 10 samples."""
        self.latencies.append(latency)
        if len(self.latencies) > 10:
            self.latencies.pop(0)

    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "consecutive_failures": self.consecutive_failures,
            "average_latency": round(self.average_latency, 3),
            "status": self.status,
            "open_until": self.open_until,
        }


class CircuitBreaker:
    """Manages circuit breakers for all configured model/providers."""

    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 900.0) -> None:
        self.healths: Dict[str, ModelHealth] = {}
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds

    def _get_health(self, model_name: str) -> ModelHealth:
        if model_name not in self.healths:
            self.healths[model_name] = ModelHealth(model_name)
        return self.healths[model_name]

    def is_available(self, model_name: str) -> bool:
        """Checks if a model provider is available to serve requests."""
        health = self._get_health(model_name)
        now = time.time()

        if health.status == "OPEN":
            if now > health.open_until:
                logger.info(f"Circuit for model '{model_name}' cooldown expired. Transitioning to HALF_OPEN.")
                health.status = "HALF_OPEN"
                return True
            return False

        return True

    def record_success(self, model_name: str, latency: float) -> None:
        """Records a successful request, resetting the circuit state."""
        health = self._get_health(model_name)
        health.record_latency(latency)
        
        if health.status != "HEALTHY":
            logger.info(f"Model '{model_name}' recovered and is now HEALTHY.")
            
        health.consecutive_failures = 0
        health.status = "HEALTHY"
        health.open_until = 0.0

    def record_failure(self, model_name: str, error_category: str) -> None:
        """Records a failure. Tripping the circuit if thresholds are exceeded."""
        health = self._get_health(model_name)
        health.consecutive_failures += 1
        health.last_failure_time = time.time()

        # Permanent failures trip the circuit breaker immediately
        is_permanent = error_category in ("QuotaExceeded", "Authentication")

        if is_permanent or health.consecutive_failures >= self.failure_threshold:
            health.status = "OPEN"
            health.open_until = time.time() + self.cooldown_seconds
            logger.warning(
                f"Tripped circuit breaker for model '{model_name}' due to "
                f"{'permanent error (' + error_category + ')' if is_permanent else str(health.consecutive_failures) + ' consecutive failures'}. "
                f"Cooldown active for {self.cooldown_seconds}s."
            )
        else:
            logger.debug(
                f"Model '{model_name}' logged failure ({health.consecutive_failures}/{self.failure_threshold})"
            )

    def get_status(self, model_name: str) -> dict:
        """Gets serializable health status for a model."""
        return self._get_health(model_name).to_dict()
