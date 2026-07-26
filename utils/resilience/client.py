"""Primary LLMClient resilient execution interface and Smolagents subclass integration."""

import os
import time
import random
import logging
from typing import Any, Dict, List, Generator

import litellm
from litellm import ModelResponse

from utils.resilience.errors import (
    classify_exception,
    AllModelsFailedError,
    AllModelsFailedError as RouterFailoverError,
)
from utils.resilience.circuit_breaker import CircuitBreaker
from utils.resilience.registry import ProviderRegistry
from utils.resilience.router import ProviderRouter
from utils.resilience.cache import RequestCache, serialize_message

logger = logging.getLogger("LLMResilience.Client")

# Global singleton managers
registry = ProviderRegistry()
circuit_breaker = CircuitBreaker()
router = ProviderRouter(registry, circuit_breaker)
request_cache = RequestCache()

METRICS_FILE = "logs/llm_resilience_metrics.json"
LOG_FILE = "logs/llm_resilience.log"


class MockChoiceMessage:
    def __init__(self, role: str, content: str, tool_calls: Any = None) -> None:
        self.role = role
        self.content = content
        self.tool_calls = tool_calls


class MockChoice:
    def __init__(self, message: MockChoiceMessage) -> None:
        self.message = message


class MockUsage:
    def __init__(self, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class MockModelResponse:
    """Mock fallback for ModelResponse if litellm.ModelResponse cannot parse cached dictionary."""

    def __init__(self, data: dict) -> None:
        choices_list = data.get("choices", [])
        self.choices = []
        for c in choices_list:
            msg_data = c.get("message", {})
            msg = MockChoiceMessage(
                role=msg_data.get("role", "assistant"),
                content=msg_data.get("content", ""),
                tool_calls=msg_data.get("tool_calls"),
            )
            self.choices.append(MockChoice(msg))

        usage_data = data.get("usage", {})
        self.usage = MockUsage(
            prompt_tokens=usage_data.get("prompt_tokens") or usage_data.get("input_tokens") or 0,
            completion_tokens=usage_data.get("completion_tokens") or usage_data.get("output_tokens") or 0,
        )
        self._data = data

    def model_dump(self) -> dict:
        return self._data


def get_resilience_metrics() -> dict:
    """Retrieves standard metrics from file."""
    if os.path.exists(METRICS_FILE):
        try:
            with open(METRICS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "total_calls": 0,
        "total_successes": 0,
        "total_failures": 0,
        "total_retries": 0,
        "total_failovers": 0,
        "errors_by_category": {
            "RateLimit": 0,
            "QuotaExceeded": 0,
            "Timeout": 0,
            "Authentication": 0,
            "ProviderUnavailable": 0,
            "Unknown": 0,
        },
        "failures_by_model": {},
    }


def save_resilience_metrics(metrics: dict) -> None:
    """Writes updated metrics back to disk."""
    import json
    os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
    try:
        with open(METRICS_FILE, "w") as f:
            json.dump(metrics, f, indent=2)
    except Exception:
        pass


def increment_resilience_metric(key_path: str) -> None:
    """Atomically increments a nested metric key."""
    import json
    metrics = get_resilience_metrics()
    parts = key_path.split(".")

    current = metrics
    for p in parts[:-1]:
        if p not in current:
            current[p] = {}
        current = current[p]

    last_part = parts[-1]
    if isinstance(current, dict):
        current[last_part] = current.get(last_part, 0) + 1

    save_resilience_metrics(metrics)


def record_resilience_log(
    event_type: str,
    model_name: str,
    message: str,
    tried_models: List[str] = None,
    error_category: str = None,
    attempt: int = None,
) -> None:
    """Appends structured JSON log files to logs/llm_resilience.log."""
    import json
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    log_record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event_type,
        "model": model_name,
        "message": message,
    }
    if tried_models is not None:
        log_record["tried_models"] = tried_models
    if error_category is not None:
        log_record["error_category"] = error_category
    if attempt is not None:
        log_record["attempt"] = attempt

    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_record) + "\n")
    except Exception:
        pass


def resilient_completion(*args, **kwargs) -> Any:
    """Primary completion wrapper implementing robust failover and retry loops."""
    requested_model = kwargs.get("model") or (args[0] if args else None)
    if not requested_model:
        raise ValueError("Model parameter is required.")

    messages = kwargs.get("messages", [])

    # 1. Cache lookup
    cached_val = request_cache.get(messages, kwargs)
    if cached_val is not None:
        try:
            return ModelResponse(**cached_val)
        except Exception:
            return MockModelResponse(cached_val)

    # 2. Main Failover Loop
    current_model = requested_model
    tried_models: List[str] = []
    max_retries = int(os.getenv("MODEL_NUM_RETRIES", "3"))
    base_delay = 1.0

    while True:
        try:
            current_model = router.select_model(current_model)
        except Exception as e:
            record_resilience_log("ALL_MODELS_FAILED", requested_model, str(e), tried_models)
            raise AllModelsFailedError(
                f"Failover exhaustion. All fallback models failed. Attempted: {tried_models}"
            ) from e

        tried_models.append(current_model)
        logger.info(f"Routing call to model '{current_model}' (Requested: '{requested_model}')")

        # Prepare kwargs for the active model configuration
        config_kwargs = kwargs.copy()
        config_kwargs["model"] = current_model
        
        resolved_config = registry.resolve_config(current_model)
        for k, v in resolved_config.items():
            if k not in config_kwargs or k == "model":
                config_kwargs[k] = v

        # 3. Retry loop for the selected model
        attempt = 0
        model_failed = False
        while attempt <= max_retries:
            start_time = time.time()
            try:
                increment_resilience_metric("total_calls")
                
                # If stream is enabled, delegate to a stream handler
                if config_kwargs.get("stream", False):
                    # For streaming, we yield chunks. We wrap it in a custom generator.
                    return _resilient_stream_generator(config_kwargs, max_retries, base_delay)

                response = litellm.completion(**config_kwargs)

                if not response.choices:
                    raise ValueError("API returned response with no choices.")

                content = response.choices[0].message.content
                if not content:
                    raise ValueError("API returned response with empty content.")

                # Partial response check (specifically for JSON validation if requested)
                is_json_requested = False
                for msg in config_kwargs.get("messages", []):
                    msg_content = str(msg.get("content", "")).lower() if isinstance(msg, dict) else str(getattr(msg, "content", "")).lower()
                    if ("json" in msg_content or "json_object" in msg_content) and "code block" not in msg_content:
                        is_json_requested = True
                        break

                if is_json_requested and "action" in content.lower() and "<code>" not in content:
                    cleaned_content = content.strip()
                    if cleaned_content.startswith("```"):
                        lines = cleaned_content.splitlines()
                        if lines[0].startswith("```json") or lines[0].startswith("```"):
                            cleaned_content = "\n".join(lines[1:-1]).strip()
                    try:
                        import json
                        json.loads(cleaned_content)
                    except Exception as json_err:
                        raise ValueError(f"Partial/Malformed JSON response: {json_err}. Content: {content[:200]}")

                # Success path
                latency = time.time() - start_time
                circuit_breaker.record_success(current_model, latency)
                request_cache.set(messages, kwargs, response)
                increment_resilience_metric("total_successes")
                return response

            except Exception as e:
                latency = time.time() - start_time
                error_obj = classify_exception(e)
                logger.warning(
                    f"LLM Call failed on attempt {attempt + 1}/{max_retries + 1} "
                    f"for model '{current_model}' ({error_obj.category}): {e}"
                )

                # Record metrics and failure logs
                increment_resilience_metric("total_failures")
                increment_resilience_metric(f"errors_by_category.{error_obj.category}")
                increment_resilience_metric(f"failures_by_model.{current_model}")
                record_resilience_log(
                    "ATTEMPT_FAILURE",
                    current_model,
                    str(e),
                    error_category=error_obj.category,
                    attempt=attempt,
                )

                circuit_breaker.record_failure(current_model, error_obj.category)

                # Route immediately if non-retryable
                is_retryable = error_obj.category in ("RateLimit", "Timeout", "ProviderUnavailable")
                if not is_retryable:
                    logger.warning(f"Permanent error '{error_obj.category}' encountered. Switching provider immediately.")
                    model_failed = True
                    break

                attempt += 1
                if attempt <= max_retries:
                    # Exponential backoff with jitter
                    delay = base_delay * (2 ** attempt)
                    jitter = random.uniform(0.1, 1.0)
                    sleep_time = min(30.0, delay + jitter)
                    logger.info(f"Sleeping for {sleep_time:.2f}s before retry...")
                    time.sleep(sleep_time)
                    increment_resilience_metric("total_retries")
                else:
                    logger.warning(f"Retry threshold reached for model '{current_model}'.")
                    model_failed = True
                    break

        if model_failed:
            increment_resilience_metric("total_failovers")
            record_resilience_log(
                "MODEL_FAILOVER",
                current_model,
                f"Model '{current_model}' failed. Swapping to next alternative.",
                tried_models,
            )
            # Route model selection dynamically next round
            current_model = ""


def _resilient_stream_generator(config_kwargs: dict, max_retries: int, base_delay: float) -> Generator[Any, None, None]:
    """Generator implementation for streaming with failover and retry support."""
    current_model = config_kwargs["model"]
    tried_models = [current_model]
    
    while True:
        attempt = 0
        stream_started = False
        yielded_chunks = []

        while attempt <= max_retries:
            try:
                # Start stream completion
                stream = litellm.completion(**config_kwargs)
                for chunk in stream:
                    stream_started = True
                    yielded_chunks.append(chunk)
                    yield chunk

                # Success
                circuit_breaker.record_success(current_model, 1.0)
                increment_resilience_metric("total_successes")
                return

            except Exception as e:
                error_obj = classify_exception(e)
                logger.warning(f"Streaming failed on attempt {attempt + 1}: {e}")
                
                increment_resilience_metric("total_failures")
                increment_resilience_metric(f"errors_by_category.{error_obj.category}")
                circuit_breaker.record_failure(current_model, error_obj.category)

                # If the stream had already yielded chunks to the caller, we cannot cleanly retry
                # because the caller has already consumed partial state. We must propagate the exception.
                if stream_started:
                    logger.error("Streaming failed mid-way after yielding content. Cannot retry stream safely.")
                    raise error_obj

                is_retryable = error_obj.category in ("RateLimit", "Timeout", "ProviderUnavailable")
                if not is_retryable:
                    break

                attempt += 1
                if attempt <= max_retries:
                    time.sleep(base_delay * (2 ** attempt) + random.uniform(0.1, 1.0))
                else:
                    break

        # If we failed to get anything from this model, switch models and try again
        increment_resilience_metric("total_failovers")
        try:
            current_model = router.select_model("")
            config_kwargs["model"] = current_model
            resolved_config = registry.resolve_config(current_model)
            for k, v in resolved_config.items():
                if k not in config_kwargs or k == "model":
                    config_kwargs[k] = v
            tried_models.append(current_model)
        except Exception as router_err:
            raise AllModelsFailedError(f"Failover stream routing exhausted. Attempted: {tried_models}") from router_err


from smolagents import LiteLLMModel

class ResilientLiteLLMModel(LiteLLMModel):
    """Resilient subclass of LiteLLMModel routing all calls through our resilient LLMClient."""

    def create_client(self) -> Any:
        """Overrides LiteLLM client mapping to point to LLMClient."""
        class ResilientClient:
            @staticmethod
            def completion(*args, **kwargs) -> Any:
                return resilient_completion(*args, **kwargs)
        return ResilientClient()
