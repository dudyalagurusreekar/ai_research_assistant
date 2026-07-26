"""Custom exceptions for LLM provider failure categorization."""

class LLMResilienceError(Exception):
    """Base exception for LLM provider resilience errors."""
    category = "Unknown"


class RateLimitError(LLMResilienceError):
    """HTTP 429 - Rate limit exceeded."""
    category = "RateLimit"


class QuotaExceededError(LLMResilienceError):
    """API quota/budget exceeded."""
    category = "QuotaExceeded"


class TimeoutError(LLMResilienceError):
    """API response timeout."""
    category = "Timeout"


class AuthenticationError(LLMResilienceError):
    """Invalid API keys or permissions."""
    category = "Authentication"


class ProviderUnavailableError(LLMResilienceError):
    """Temporary provider outage or server overload."""
    category = "ProviderUnavailable"


class RetryExhaustedError(LLMResilienceError):
    """Maximum retry count exceeded for a single provider."""
    category = "ProviderUnavailable"


class AllModelsFailedError(LLMResilienceError):
    """Failover chain completely exhausted; all fallback models failed."""
    category = "ProviderUnavailable"


def classify_exception(exc: Exception) -> LLMResilienceError:
    """Classifies raw API exceptions into one of our five resilient error categories."""
    exc_type_name = type(exc).__name__
    exc_msg = str(exc).lower()

    # 1. Quota Exceeded (some providers throw this as RateLimitError, so check message content first)
    if "quota" in exc_msg or "billing" in exc_msg or "credit" in exc_msg or "budget" in exc_msg:
        return QuotaExceededError(f"Quota Exceeded: {exc}")

    # 2. Rate Limit (429)
    if "ratelimit" in exc_type_name.lower() or "429" in exc_msg or "rate limit" in exc_msg:
        return RateLimitError(f"Rate Limit: {exc}")

    # 3. Timeout
    if "timeout" in exc_type_name.lower() or "timeout" in exc_msg or "timed out" in exc_msg:
        return TimeoutError(f"API Timeout: {exc}")

    # 4. Authentication / API Key issues
    if (
        "authentication" in exc_type_name.lower() or
        "401" in exc_msg or
        "403" in exc_msg or
        "api key" in exc_msg or
        "unauthorized" in exc_msg
    ):
        return AuthenticationError(f"Authentication Error: {exc}")

    # 5. Connection failures / Temporary provider outages
    if (
        "connection" in exc_type_name.lower() or
        "connection" in exc_msg or
        "503" in exc_msg or
        "502" in exc_msg or
        "500" in exc_msg or
        "serviceunavailable" in exc_type_name.lower() or
        "service unavailable" in exc_msg or
        "overloaded" in exc_msg or
        "bad gateway" in exc_msg or
        "internal server error" in exc_msg or
        "temporary" in exc_msg or
        "refused" in exc_msg or
        "reset" in exc_msg
    ):
        return ProviderUnavailableError(f"Provider Unavailable: {exc}")

    # Default fallback
    return LLMResilienceError(f"LLM Failure: {exc}")
