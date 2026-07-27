"""Circuit Breaker and Provider Failover resilience mechanisms."""

import time
from enum import Enum
from typing import List, Optional


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Tripped / blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """Monitors failures and trips circuit when failure threshold is exceeded."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout_seconds: float = 30.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_seconds
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        self.last_state_change = time.time()

    def can_execute(self) -> bool:
        """Check if execution is permitted through the circuit breaker."""
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_state_change > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = time.time()
                return True
            return False
        if self.state == CircuitState.HALF_OPEN:
            return True
        return False

    def record_success(self) -> None:
        """Record successful execution and reset circuit to CLOSED."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record a failure and trip circuit if threshold reached."""
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()


class ProviderFailover:
    """Manages primary and fallback LLM model providers."""

    def __init__(self, providers: Optional[List[str]] = None) -> None:
        self.providers = providers or ["gemini/gemini-1.5-flash", "openai/gpt-4o-mini"]
        self.current_index = 0

    def get_current_provider(self) -> str:
        """Return active primary model provider."""
        return self.providers[self.current_index]

    def failover(self) -> str:
        """Switch to next fallback provider in chain."""
        if len(self.providers) > 1:
            self.current_index = (self.current_index + 1) % len(self.providers)
        return self.get_current_provider()
