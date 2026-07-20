import os
from dotenv import load_dotenv
from smolagents import LiteLLMModel

load_dotenv()


def create_model():
    provider = os.getenv("MODEL_PROVIDER", "ollama").lower()

    if provider == "ollama":
        model_name = os.getenv("MODEL_NAME", "ollama_chat/qwen2:7b")
        if not model_name.startswith("ollama"):
            model_name = f"ollama_chat/{model_name}"
        elif model_name.startswith("ollama/") and not model_name.startswith("ollama_chat/"):
            model_name = model_name.replace("ollama/", "ollama_chat/", 1)

        return LiteLLMModel(
            model_id=model_name,
            api_base=os.getenv("MODEL_API_BASE", "http://127.0.0.1:11434"),
            api_key=os.getenv("MODEL_API_KEY") or None,
            flatten_messages_as_text=False,
            timeout=120,
            temperature=0.2,
            max_tokens=2048,
        )

    raise ValueError(f"Unsupported provider: {provider}")