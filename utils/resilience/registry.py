"""Provider registry for resolving model-specific configurations and credentials."""

import os
from typing import Dict, Any, List


class ProviderRegistry:
    """Manages LLM provider configurations, credentials, and priorities."""

    def __init__(self) -> None:
        self.default_fallbacks = [
            "ollama_chat/phi3:latest",
            "gemini/gemini-2.5-flash",
            "gemini/gemini-1.5-flash",
            "openai/gpt-4o-mini",
            "anthropic/claude-3-5-haiku",
        ]

    def get_configured_providers(self) -> List[str]:
        """Returns a list of model names that are configured and have valid credentials."""
        primary = os.getenv("MODEL_NAME", "gemini/gemini-2.5-flash").strip()
        chain = [primary]

        # Add environment-configured fallback models
        fallback_str = os.getenv("FALLBACK_MODELS", "")
        if fallback_str:
            for m in fallback_str.split(","):
                m = m.strip()
                if m and m not in chain:
                    chain.append(m)
        else:
            # Fall back to default fallback chain
            for m in self.default_fallbacks:
                if m not in chain:
                    chain.append(m)

        # Filter out models that lack the necessary API keys, unless they are local Ollama
        configured = []
        for model in chain:
            if self.is_provider_configured(model):
                configured.append(model)

        return configured

    def is_provider_configured(self, model_name: str) -> bool:
        """Determines if the API keys/endpoints for the requested model are configured."""
        if model_name.startswith(("ollama/", "ollama_chat/")):
            return True

        # Check for specific API keys
        if model_name.startswith("gemini/") and os.getenv("GEMINI_API_KEY"):
            return True
        if model_name.startswith("openai/") and os.getenv("OPENAI_API_KEY"):
            return True
        if model_name.startswith("anthropic/") and os.getenv("ANTHROPIC_API_KEY"):
            return True

        # Fallback general API key
        if os.getenv("MODEL_API_KEY"):
            return True

        return False

    def resolve_config(self, model_name: str) -> Dict[str, Any]:
        """Resolves the kwargs (API key, base URL, timeout, parameters) for a specific model."""
        api_key = ""
        if model_name.startswith("gemini/"):
            api_key = os.getenv("GEMINI_API_KEY", "").strip()
        elif model_name.startswith("openai/"):
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
        elif model_name.startswith("anthropic/"):
            api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

        if not api_key:
            api_key = os.getenv("MODEL_API_KEY", "").strip()

        config: Dict[str, Any] = {
            "model": model_name,
            "temperature": 0.0,
            "max_tokens": int(os.getenv("MODEL_MAX_TOKENS", "1536")),
            "timeout": int(os.getenv("MODEL_TIMEOUT", "300")),
            "drop_params": True,
        }

        if api_key:
            config["api_key"] = api_key

        if model_name.startswith(("ollama/", "ollama_chat/")):
            config["api_base"] = os.getenv("MODEL_API_BASE", "http://127.0.0.1:11434")
            config["num_ctx"] = int(os.getenv("MODEL_NUM_CTX", "8192"))
        else:
            api_base = os.getenv("MODEL_API_BASE", "").strip()
            if api_base:
                config["api_base"] = api_base

        return config
