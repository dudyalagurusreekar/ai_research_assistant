import os
from typing import Dict, Any, Tuple
from dotenv import load_dotenv
from smolagents import LiteLLMModel, MessageRole
import litellm

load_dotenv()


def resolve_model_config() -> Tuple[str, Dict[str, Any]]:
    """
    Resolves the model ID, API keys, and provider-specific kwargs dynamically
    from environment variables.
    """
    model_name = os.getenv("MODEL_NAME", "gemini/gemini-2.5-flash").strip()

    # If no provider prefix is supplied and it's a raw model tag like 'phi3:latest', default to ollama_chat
    if "/" not in model_name:
        model_name = f"ollama_chat/{model_name}"

    # Determine API key based on provider prefix or MODEL_API_KEY fallback
    api_key = os.getenv("MODEL_API_KEY", "").strip()
    if not api_key:
        if model_name.startswith("gemini/"):
            api_key = os.getenv("GEMINI_API_KEY", "").strip()
        elif model_name.startswith("openai/"):
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
        elif model_name.startswith("anthropic/"):
            api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    # Base configuration kwargs
    model_kwargs: Dict[str, Any] = {
        "flatten_messages_as_text": False,
        "custom_role_conversions": {
            MessageRole.USER: "user",
            MessageRole.SYSTEM: "system",
            MessageRole.ASSISTANT: "assistant",
            MessageRole.TOOL_CALL: "assistant",
            MessageRole.TOOL_RESPONSE: "user",
        },
        "temperature": 0.0,
        "max_tokens": int(os.getenv("MODEL_MAX_TOKENS", "512")),
        "drop_params": True,  # Allows LiteLLM to drop unsupported parameters per provider
        "timeout": int(os.getenv("MODEL_TIMEOUT", "300")),
    }

    if api_key:
        model_kwargs["api_key"] = api_key

    # Provider-specific configurations
    if model_name.startswith("ollama/") or model_name.startswith("ollama_chat/"):
        model_kwargs["api_base"] = os.getenv("MODEL_API_BASE", "http://127.0.0.1:11434")
        model_kwargs["num_ctx"] = int(os.getenv("MODEL_NUM_CTX", "8192"))
    else:
        # For non-Ollama models, set api_base if explicitly set in environment
        api_base = os.getenv("MODEL_API_BASE", "").strip()
        if api_base:
            model_kwargs["api_base"] = api_base

    return model_name, model_kwargs


def get_model() -> LiteLLMModel:
    """
    Factory to construct a LiteLLMModel instance.
    """
    model_name, model_kwargs = resolve_model_config()

    if os.getenv("DEBUG", "false").lower() == "true":
        litellm._turn_on_debug()

    return LiteLLMModel(
        model_id=model_name,
        **model_kwargs,
    )


def validate_model_connection() -> Tuple[bool, str]:
    """
    Validates model reachability and configuration prior to running the agent loop.
    Returns (is_valid, message).
    """
    model_name, model_kwargs = resolve_model_config()

    try:
        # Quick validation completion ping
        kwargs = {
            "model": model_name,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 5,
            "timeout": 15,
        }
        if "api_key" in model_kwargs:
            kwargs["api_key"] = model_kwargs["api_key"]
        if "api_base" in model_kwargs:
            kwargs["api_base"] = model_kwargs["api_base"]

        litellm.completion(**kwargs)
        return True, f"Model '{model_name}' verified successfully."
    except Exception as e:
        return False, f"Model connection check failed for '{model_name}': {str(e)}"
