"""LLM Resilience Package.

Provides robust retry mechanisms, dynamic circuit breaking, health status, 
caching, and provider failover routing for the LLM execution layer.
"""

from utils.resilience.errors import (
    LLMResilienceError,
    RateLimitError,
    QuotaExceededError,
    TimeoutError,
    AuthenticationError,
    ProviderUnavailableError,
    RetryExhaustedError,
    AllModelsFailedError,
    classify_exception,
)

from utils.resilience.circuit_breaker import (
    ModelHealth,
    CircuitBreaker,
)

from utils.resilience.registry import (
    ProviderRegistry,
)

from utils.resilience.router import (
    ProviderRouter,
)

from utils.resilience.cache import (
    RequestCache,
)

from utils.resilience.client import (
    resilient_completion,
    ResilientLiteLLMModel,
    get_resilience_metrics,
    save_resilience_metrics,
    registry,
    circuit_breaker,
    router,
    request_cache,
)

__all__ = [
    "LLMResilienceError",
    "RateLimitError",
    "QuotaExceededError",
    "TimeoutError",
    "AuthenticationError",
    "ProviderUnavailableError",
    "RetryExhaustedError",
    "AllModelsFailedError",
    "classify_exception",
    "ModelHealth",
    "CircuitBreaker",
    "ProviderRegistry",
    "ProviderRouter",
    "RequestCache",
    "resilient_completion",
    "ResilientLiteLLMModel",
    "get_resilience_metrics",
    "save_resilience_metrics",
    "registry",
    "circuit_breaker",
    "router",
    "request_cache",
]
